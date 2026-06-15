from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.utils.statistics import get_emotion_profile_from_raw_data, get_global_averages


class EmotionRange(BaseModel):
    concentration: tuple[float, float]
    relaxation: tuple[float, float]


class EmotionCenter(BaseModel):
    concentration: float
    relaxation: float


class RangesResponse(BaseModel):
    status: str = "success"
    global_average: dict[str, float]
    emotion_ranges: dict[str, EmotionRange]
    emotion_centers: dict[str, EmotionCenter]


router = APIRouter(prefix="/api", tags=["ranges"])


@router.get(
    "/ranges",
    response_model=RangesResponse,
    status_code=200,
)
async def get_ranges(
    session: AsyncSession = Depends(get_db_session),
) -> RangesResponse:
    global_averages = await get_global_averages(session)
    emotion_profile = await get_emotion_profile_from_raw_data(session)

    emotion_ranges = {}
    for emotion, ranges in emotion_profile["ranges"].items():
        emotion_ranges[emotion] = EmotionRange(
            concentration=ranges["concentration"],
            relaxation=ranges["relaxation"],
        )

    emotion_centers = {}
    for emotion, center in emotion_profile["centers"].items():
        emotion_centers[emotion] = EmotionCenter(
            concentration=center["concentration"],
            relaxation=center["relaxation"],
        )

    return RangesResponse(
        global_average={
            "concentration": float(global_averages["avg_concentration"]),
            "relaxation": float(global_averages["avg_relaxation"]),
            "total_records": int(global_averages["total_records"]),
        },
        emotion_ranges=emotion_ranges,
        emotion_centers=emotion_centers,
    )
