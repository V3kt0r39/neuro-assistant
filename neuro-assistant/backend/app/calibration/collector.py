from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EEGRecord, User
from app.utils.validators import CalibrationRequest


async def save_calibration_record(session: AsyncSession, payload: CalibrationRequest) -> EEGRecord:
    user = await session.scalar(select(User).where(User.id == payload.user_id))
    if user is None:
        raise ValueError("Calibration user was not found.")
    if not user.is_calibration_user:
        raise ValueError("The provided user is not marked as a calibration user.")

    record = EEGRecord(
        user_id=payload.user_id,
        concentration=payload.concentration,
        relaxation=payload.relaxation,
        self_reported_emotion=payload.self_reported_emotion.value,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record