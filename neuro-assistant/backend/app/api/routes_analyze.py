from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.connection import get_db_session
from app.production.recommendation_engine import get_ai_recommendation
from app.utils.logger import get_logger, log_incoming, log_processed, log_rejected
from app.utils.statistics import get_emotion_profile_from_raw_data, get_global_averages
from app.utils.validators import AnalyzeErrorResponse, AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/api", tags=["analyze"])
logger = get_logger(__name__)
settings = get_settings()

HIGH_INTERFERENCE_MESSAGE = "Interference level is too high. Please adjust your headset."


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": AnalyzeErrorResponse,
            "description": "Request rejected due to high EEG interference.",
        }
    },
)
async def analyze(
    payload: AnalyzeRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AnalyzeResponse | JSONResponse:
    log_incoming(
        concentration=payload.concentration,
        relaxation=payload.relaxation,
        poor_signal=payload.poor_signal,
    )
    if payload.poor_signal > settings.poor_signal_threshold:
        log_rejected(
            concentration=payload.concentration,
            relaxation=payload.relaxation,
            poor_signal=payload.poor_signal,
            reason="high_interference",
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "error": "high_interference",
                "message": HIGH_INTERFERENCE_MESSAGE,
                "details": {
                    "concentration": payload.concentration,
                    "relaxation": payload.relaxation,
                    "poor_signal": payload.poor_signal,
                },
            },
        )

    global_averages = await get_global_averages(session)
    emotion_profile = await get_emotion_profile_from_raw_data(session)
    try:
        ai_result = await get_ai_recommendation(
            concentration=payload.concentration,
            relaxation=payload.relaxation,
            global_avg_concentration=float(global_averages["avg_concentration"]),
            global_avg_relaxation=float(global_averages["avg_relaxation"]),
            emotion_ranges=emotion_profile["ranges"],
            emotion_centers=emotion_profile["centers"],
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to generate AI recommendation via Ollama")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate AI recommendation.",
        ) from exc

    detected_emotion = str(ai_result["emotion"])
    recommendation = str(ai_result["recommendation"])
    deviation = ai_result["deviation"]
    deviation_concentration = float(deviation["concentration"])  # type: ignore[index]
    deviation_relaxation = float(deviation["relaxation"])  # type: ignore[index]

    log_processed(
        emotion=detected_emotion,
        concentration=payload.concentration,
        relaxation=payload.relaxation,
        global_avg_concentration=float(global_averages["avg_concentration"]),
        global_avg_relaxation=float(global_averages["avg_relaxation"]),
        recommendation=recommendation,
    )
    return AnalyzeResponse(
        status="success",
        detected_emotion=detected_emotion,  # type: ignore[arg-type]
        ai_recommendation=recommendation,
        current_state={
            "concentration": payload.concentration,
            "relaxation": payload.relaxation,
        },
        global_average={
            "concentration": float(global_averages["avg_concentration"]),
            "relaxation": float(global_averages["avg_relaxation"]),
            "total_records": int(global_averages["total_records"]),
        },
        deviation={
            "concentration": deviation_concentration,
            "relaxation": deviation_relaxation,
        },
    )
