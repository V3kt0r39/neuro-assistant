from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.calibration.collector import save_calibration_record
from app.database.connection import get_db_session
from app.utils.validators import CalibrationRequest, CalibrationResponse

router = APIRouter(prefix="/api", tags=["calibration"])


@router.post(
    "/calibrate",
    response_model=CalibrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def calibrate(
    payload: CalibrationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> CalibrationResponse:
    try:
        record = await save_calibration_record(session, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return CalibrationResponse(status="success", record_id=record.id)