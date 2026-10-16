"""DEMO / TEST DATA only: persistence contracts, never seeded into production."""
import json
from uuid import uuid4
import pytest
from pydantic import ValidationError
from backend.app.schemas.patient_history import AnalysisRecord, ScanRecord
from ml.explanation.engine import VisualExplanationEngine
from ml.explanation.schema import ExplanationResult


def test_scan_serialization_and_side():
    scan = ScanRecord(id=uuid4(), user_id=uuid4(), scan_date="2026-01-01", body_part="mixed")
    assert scan.body_side is None
    assert json.loads(scan.model_dump_json())["body_part"] == "mixed"
    assert ScanRecord(**{**scan.model_dump(), "body_part": "unknown", "body_side": "left"}).body_side == "left"
    with pytest.raises(ValidationError):
        ScanRecord(**{**scan.model_dump(), "body_side": "inferred_left"})


def test_private_path_validation():
    fields = dict(id=uuid4(), user_id=uuid4(), scan_date="2026-01-01")
    valid = f'{fields["user_id"]}/{fields["id"]}/test.png'
    assert ScanRecord(**fields, storage_path=valid).storage_path == valid
    for path in [f"{uuid4()}/{fields['id']}/test.png", valid + "/../../secret", "https://example.com/xray.png"]:
        with pytest.raises(ValidationError):
            ScanRecord(**fields, storage_path=path)


@pytest.mark.parametrize("part", ["hand", "leg", "hip", "shoulder", "mixed", "unknown"])
def test_stage5_storage_roundtrip(part):
    explanation = VisualExplanationEngine().explain({
        "xray_validation": {"is_xray": True, "confidence": .99},
        "body_part": {"result": part, "confidence": .9},
        "abnormality": {"result": "uncertain", "confidence": .4, "fracture_probability": .4},
    })
    explanation.attention.overlay_base64 = "data:image/png;base64,TEST_ONLY"
    record = AnalysisRecord(scan_id=uuid4(), user_id=uuid4(), explanation=explanation)
    payload = record.persistence_payload()
    restored = ExplanationResult.model_validate(payload["explanation"])
    assert restored.summary == explanation.summary
    assert restored.body_part.id.value == part
    assert restored.attention.overlay_base64 is None
    assert "TEST_ONLY" not in json.dumps(payload)
    assert explanation.attention.overlay_base64 is not None  # No input mutation.
    assert payload["analysis_status"] == explanation.analysis_status.value


def test_confidence_and_unsupported_body_validation():
    with pytest.raises(ValidationError):
        ScanRecord(id=uuid4(), user_id=uuid4(), scan_date="2026-01-01", body_part="chest")
    explanation = VisualExplanationEngine().explain({"xray_validation": {}, "body_part": {}})
    with pytest.raises(ValidationError):
        AnalysisRecord(scan_id=uuid4(), user_id=uuid4(), explanation=explanation, fracture_confidence=1.5)
