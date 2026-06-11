from sqlalchemy.ext.asyncio import AsyncSession


async def calculate_and_store_thresholds(session: AsyncSession) -> list[object]:
    raise RuntimeError(
        "Calibration thresholds are deprecated in the current specification. "
        "Use POST /api/analyze for production inference."
    )


async def get_thresholds(session: AsyncSession) -> list[object]:
    raise RuntimeError(
        "Calibration thresholds are deprecated in the current specification. "
        "Use POST /api/analyze for production inference."
    )
