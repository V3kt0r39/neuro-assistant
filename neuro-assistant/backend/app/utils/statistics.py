from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DataOriginal
from app.production.emotion_detector import (
    DEFAULT_EMOTION_CENTERS,
    DEFAULT_EMOTION_RANGES,
    EmotionProfile,
    build_emotion_profile_from_points,
)


async def get_global_averages(session: AsyncSession) -> dict[str, float | int]:
    query = select(
        func.sum(DataOriginal.concentration),
        func.sum(DataOriginal.relaxation),
        func.count(),
    )
    result = await session.execute(query)
    sum_concentration, sum_relaxation, total_records = result.one()

    records_count = int(total_records or 0)
    if records_count == 0:
        return {
            "avg_concentration": 0.0,
            "avg_relaxation": 0.0,
            "total_records": 0,
        }

    avg_concentration = float(sum_concentration or 0) / records_count
    avg_relaxation = float(sum_relaxation or 0) / records_count
    return {
        "avg_concentration": round(avg_concentration, 2),
        "avg_relaxation": round(avg_relaxation, 2),
        "total_records": records_count,
    }


async def get_emotion_profile_from_raw_data(session: AsyncSession) -> EmotionProfile:
    query = select(DataOriginal.concentration, DataOriginal.relaxation)
    result = await session.execute(query)
    rows = result.all()
    points = [(float(concentration), float(relaxation)) for concentration, relaxation in rows]
    if not points:
        return {
            "ranges": DEFAULT_EMOTION_RANGES,
            "centers": DEFAULT_EMOTION_CENTERS,
        }
    return build_emotion_profile_from_points(points)
