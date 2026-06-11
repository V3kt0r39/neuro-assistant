from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DataOriginal


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
