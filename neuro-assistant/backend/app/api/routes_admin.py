from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.calibration.analyzer import calculate_and_store_thresholds, get_thresholds
from app.database.connection import get_db_session
from app.database.models import EmotionThreshold
from app.utils.validators import CalculateRangesResponse, Emotion, ThresholdOut

router = APIRouter(prefix="/api", tags=["admin"])


def serialize_threshold(threshold: EmotionThreshold) -> ThresholdOut:
    return ThresholdOut(
        emotion=Emotion(threshold.emotion),
        conc_avg=threshold.conc_avg,
        relax_avg=threshold.relax_avg,
        conc_min=threshold.conc_min,
        conc_max=threshold.conc_max,
        relax_min=threshold.relax_min,
        relax_max=threshold.relax_max,
        sample_count=threshold.sample_count,
    )


@router.post(
    "/calculate-ranges",
    response_model=CalculateRangesResponse,
    status_code=status.HTTP_200_OK,
)
async def calculate_ranges(
    session: AsyncSession = Depends(get_db_session),
) -> CalculateRangesResponse:
    try:
        thresholds = await calculate_and_store_thresholds(session)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return CalculateRangesResponse(
        status="success",
        thresholds=[serialize_threshold(item) for item in thresholds],
    )


@router.get("/thresholds", response_model=list[ThresholdOut], status_code=status.HTTP_200_OK)
async def list_thresholds(session: AsyncSession = Depends(get_db_session)) -> list[ThresholdOut]:
    thresholds = await get_thresholds(session)
    return [serialize_threshold(item) for item in thresholds]