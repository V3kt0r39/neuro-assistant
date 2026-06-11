from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["deprecated"])

DEPRECATED_MESSAGE = (
    "Calibration endpoints are deprecated in the current specification. "
    "Use POST /api/analyze with concentration, relaxation, poor_signal."
)


@router.post("/calculate-ranges")
async def calculate_ranges() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={"status": "error", "error": "deprecated_endpoint", "message": DEPRECATED_MESSAGE},
    )


@router.get("/thresholds")
async def list_thresholds() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={"status": "error", "error": "deprecated_endpoint", "message": DEPRECATED_MESSAGE},
    )
