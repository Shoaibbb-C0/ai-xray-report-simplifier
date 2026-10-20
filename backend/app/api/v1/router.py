"""API v1 Router definitions."""

from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.ml_service import ml_service
from backend.app.api.v1.analysis import router as analysis_router

router = APIRouter()
router.include_router(analysis_router)


@router.get("/health")
def api_health():
    """V1 Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
    }


@router.get("/status")
def system_status():
    """System and ML engine readiness status."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "ml_engine": ml_service.get_service_status(),
    }
