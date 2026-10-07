"""API v1 Router definitions."""

from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.ml_service import ml_service

router = APIRouter()


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
