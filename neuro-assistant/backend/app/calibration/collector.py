from sqlalchemy.ext.asyncio import AsyncSession


async def save_calibration_record(session: AsyncSession, payload: object) -> object:
    raise RuntimeError(
        "Calibration record collection is deprecated in the current specification. "
        "Use POST /api/analyze for production inference."
    )
