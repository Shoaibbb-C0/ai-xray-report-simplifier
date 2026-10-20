"""Software contracts use explicit mocks, never stand in for trained evaluation."""
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ml_service import MLInferenceService, ModelBusyError, ModelNotLoadedError, ml_service
from ml.explanation.engine import VisualExplanationEngine
from ml.inference.stage3_pipeline import Stage3InferencePipeline
from ml.inference.fracture_classifier import FractureInferenceEngine


def image_bytes(format="PNG", size=(100, 100)):
    stream = BytesIO()
    Image.new("RGB", size, "gray").save(stream, format=format)
    return stream.getvalue()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("data,mime,status,code", [
    (b"not an image", "image/png", 422, "invalid_image"),
    (b"<svg/>", "image/svg+xml", 415, "unsupported_type"),
    (image_bytes("GIF"), "image/png", 415, "unsupported_type"),
    (image_bytes(size=(20, 100)), "image/png", 422, "invalid_dimensions"),
    (b"x" * (10 * 1024 * 1024 + 1), "image/png", 413, "file_too_large"),
    (image_bytes()[:30], "image/png", 422, "invalid_image"),
    (image_bytes("JPEG")[:-50], "image/jpeg", 422, "invalid_image"),
], ids=["corrupt", "svg", "spoofed_format", "small_dimensions", "oversized", "truncated_png", "truncated_jpeg"])
def test_invalid_uploads(client, data, mime, status, code):
    response = client.post("/api/v1/analyze", files={"file": ("../../private.png", data, mime)})
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert "private.png" not in response.text


def test_no_models_fails_closed(client, monkeypatch):
    monkeypatch.setattr(ml_service, "pipeline", None)
    response = client.post("/api/v1/analyze", files={"file": ("image.png", image_bytes(), "image/png")})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_unavailable"
    assert client.get("/ready").status_code == 503


def test_jpeg_orientation_matches_browser_preview():
    from backend.app.api.v1.analysis import decode_image
    stream = BytesIO()
    with Image.new("RGB", (100,80), "gray") as source:
        exif = source.getexif()
        exif[274] = 6
        source.save(stream, format="JPEG", exif=exif)
    with decode_image(stream.getvalue()) as decoded:
        assert decoded.size == (80,100)
        assert decoded.getexif().get(274) is None


def test_success_contract_and_image_cleanup(client, monkeypatch):
    seen = []
    def predict(image, language, attention):
        seen.append(image)
        assert image.size == (100, 100)
        return {"status": "TEST_ONLY", "persistence": {"saved": False}, "language": language}
    monkeypatch.setattr(ml_service, "run_inference", predict)
    response = client.post("/api/v1/analyze", files={"file": ("a.png", image_bytes(), "image/png")}, data={"language": "mr"})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json()["persistence"]["saved"] is False
    assert response.json()["language"] == "mr"
    with pytest.raises(ValueError):
        seen[0].getpixel((0, 0))


def test_unexpected_error_does_not_expose_paths(client, monkeypatch):
    def broken(*args):
        raise RuntimeError("C:/private/patient/image.png")
    monkeypatch.setattr(ml_service, "run_inference", broken)
    response = client.post("/api/v1/analyze", files={"file": ("a.png", image_bytes(), "image/png")})
    assert response.status_code == 500
    assert "private" not in response.text


def test_language_and_cors(client):
    response = client.post("/api/v1/analyze", files={"file": ("a.png", image_bytes(), "image/png")}, data={"language": "fr"})
    assert response.status_code == 422
    response = client.options("/api/v1/analyze", headers={"Origin": "https://untrusted.invalid", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in response.headers
    response = client.post("/api/v1/analyze", headers={"Origin": "https://untrusted.invalid"}, files={"file": ("a.png", image_bytes(), "image/png")})
    assert response.status_code == 403


def test_missing_checkpoints_never_allow_random_inference(tmp_path):
    with pytest.raises(FileNotFoundError):
        Stage3InferencePipeline(validator_checkpoint=tmp_path / "missing.pt")
    with pytest.raises(FileNotFoundError):
        FractureInferenceEngine(checkpoint_path=tmp_path / "missing.pt")


def test_corrupt_checkpoint_fails_closed(tmp_path):
    path = tmp_path / "corrupt.pt"
    path.write_bytes(b"invalid test checkpoint")
    with pytest.raises(Exception):
        FractureInferenceEngine(checkpoint_path=path)


def test_checkpoint_checksum_mismatch_is_rejected(tmp_path):
    import json
    from ml.inference.model_files import model_metadata
    path = tmp_path / "test-only.pt"
    path.write_bytes(b"SOFTWARE TEST ONLY - NOT TRAINED WEIGHTS")
    (tmp_path / "model_metadata.json").write_text(json.dumps({"sha256": "0" * 64}))
    with pytest.raises(ValueError, match="checksum"):
        model_metadata(path)


@pytest.mark.parametrize("status,validation,expected", [
    ("REJECTED_NON_XRAY", {"result": "non_xray", "confidence": .99}, "NON_XRAY"),
    ("REJECTED_UNCERTAIN_VALIDATION", {"result": "uncertain", "confidence": .55}, "XRAY_VALIDATION_UNCERTAIN"),
    ("MODEL_UNAVAILABLE", None, "MODEL_UNAVAILABLE"),
    ("ERROR", None, "ERROR"),
])
def test_real_cascade_null_sections_and_rejections(status, validation, expected):
    explanation = VisualExplanationEngine().explain({"pipeline_status": status, "xray_validation": validation, "body_part": None, "abnormality": None})
    assert explanation.analysis_status.value == expected
    assert not explanation.attention.available


def test_service_busy_and_nonfinite_output():
    service = MLInferenceService()
    service.pipeline = Mock()
    service._lock.acquire()
    with pytest.raises(ModelBusyError):
        service.run_inference(None)
    service._lock.release()
    service.pipeline.predict.return_value = {"xray_validation": {"confidence": float("nan")}}
    with pytest.raises(Exception, match="valid result"):
        service.run_inference(None)
    assert service._lock.acquire(blocking=False)
    service._lock.release()
