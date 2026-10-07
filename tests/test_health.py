"""Foundation tests for FastAPI backend and health endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ml_service import ml_service, ModelNotLoadedError

client = TestClient(app)


def test_root_health_endpoint():
    """Verify GET /health returns HTTP 200 and standard status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-xray-backend"


def test_api_v1_health_endpoint():
    """Verify GET /api/v1/health returns HTTP 200 and version information."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_system_status_reports_uninitialized_ml():
    """Verify system status reports ML engine as not yet ready/loaded."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["ml_engine"]["ready"] is False
    assert data["ml_engine"]["loaded_models_count"] == 0


def test_placeholder_ml_service_blocks_inference():
    """Confirm ML service rejects inference calls before models are trained/loaded."""
    assert not ml_service.is_ready
    with pytest.raises(ModelNotLoadedError):
        ml_service.run_inference(None)
