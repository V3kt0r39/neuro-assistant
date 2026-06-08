from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.database.models import EmotionThreshold, UserSession
from app.production.emotion_detector import detect_emotion
from app.production.recommendation_engine import fallback_recommendation, get_ai_recommendation
from app.utils.logger import get_logger
from app.utils.validators import AnalyzeRequest, AnalyzeResponse, Emotion

router = APIRouter(prefix="/api", tags=["production"])
logger = get_logger(__name__)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze(
    payload: AnalyzeRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AnalyzeResponse:
    thresholds = list((await session.execute(select(EmotionThreshold))).scalars().all())
    try:
        detection = detect_emotion(
            concentration=payload.concentration,
            relaxation=payload.relaxation,
            thresholds=thresholds,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    recommendation_source = "ollama"
    try:
        ai_recommendation = await get_ai_recommendation(
            emotion=detection.detected_emotion,
            concentration=payload.concentration,
            relaxation=payload.relaxation,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ollama request failed, fallback recommendation will be used: %s", exc)
        ai_recommendation = fallback_recommendation(detection.detected_emotion)
        recommendation_source = "fallback"

    session_token = str(uuid4())
    session_record = UserSession(
        session_token=session_token,
        detected_emotion=detection.detected_emotion,
        concentration=payload.concentration,
        relaxation=payload.relaxation,
        ai_recommendation=ai_recommendation,
    )
    session.add(session_record)
    await session.commit()

    return AnalyzeResponse(
        status="success",
        detected_emotion=Emotion(detection.detected_emotion),
        ai_recommendation=ai_recommendation,
        session_token=session_token,
        detection_method=detection.method,
        recommendation_source=recommendation_source,
    )