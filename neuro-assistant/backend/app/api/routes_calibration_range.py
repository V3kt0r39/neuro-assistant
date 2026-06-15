from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.connection import get_db_session
from app.utils.statistics import get_global_averages

settings = get_settings()


class ParameterRange(BaseModel):
    min: float
    max: float
    step: float
    unit: str


class CalibrationRangeResponse(BaseModel):
    status: str = "success"
    concentration: ParameterRange
    relaxation: ParameterRange
    poor_signal: ParameterRange
    poor_signal_threshold: int
    global_average: dict[str, float]
    total_records: int


router = APIRouter(prefix="/api", tags=["calibration"])


@router.get(
    "/calibration-range",
    response_model=CalibrationRangeResponse,
    status_code=200,
)
async def get_calibration_range(
    session: AsyncSession = Depends(get_db_session),
) -> CalibrationRangeResponse:
    global_averages = await get_global_averages(session)

    return CalibrationRangeResponse(
        concentration=ParameterRange(
            min=0.0,
            max=100.0,
            step=0.1,
            unit="%",
        ),
        relaxation=ParameterRange(
            min=0.0,
            max=100.0,
            step=0.1,
            unit="%",
        ),
        poor_signal=ParameterRange(
            min=0.0,
            max=100.0,
            step=1.0,
            unit="%",
        ),
        poor_signal_threshold=settings.poor_signal_threshold,
        global_average={
            "concentration": float(global_averages["avg_concentration"]),
            "relaxation": float(global_averages["avg_relaxation"]),
        },
        total_records=int(global_averages["total_records"]),
    )
