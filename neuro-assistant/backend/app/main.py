from fastapi import FastAPI

from app.api.routes_admin import router as admin_router
from app.api.routes_calibration import router as calibration_router
from app.api.routes_production import router as production_router
from app.config import get_settings
from app.utils.logger import configure_logging

settings = get_settings()
configure_logging("DEBUG" if settings.debug else "INFO")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(calibration_router)
app.include_router(admin_router)
app.include_router(production_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "message": "Neuro Assistant backend is running.",
        "docs": "/docs",
    }


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}