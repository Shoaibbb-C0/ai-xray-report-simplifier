"""Automated integration tests for Stage 4 Cascaded Inference Pipeline and safety gates."""

from pathlib import Path
from PIL import Image
import pytest

from ml.inference.fracture_classifier import FractureInferenceEngine, DEFAULT_CKPT
from ml.inference.stage3_pipeline import VALIDATOR_CKPT, BODY_PART_CKPT
from ml.inference.stage4_pipeline import Stage4InferencePipeline


@pytest.fixture
def trained_checkpoints():
    for path in (VALIDATOR_CKPT, BODY_PART_CKPT, DEFAULT_CKPT):
        if not path.is_file():
            pytest.skip(f"Trained checkpoint is missing: {path.name}; real inference is blocked")


@pytest.fixture
def sample_white_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color=(255, 255, 255))
    p = tmp_path / "white.png"
    img.save(p)
    return p


@pytest.fixture
def sample_orange_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color=(255, 128, 0))
    p = tmp_path / "orange.png"
    img.save(p)
    return p


@pytest.fixture
def real_xray_image() -> Path:
    sample_p = Path("ml/learning/sample_image.png")
    if sample_p.exists():
        return sample_p
    # Fallback to fracatlas image
    frac_p = Path("ml/datasets/raw/fracatlas/FracAtlas/images/Non_fractured/IMG0000000.jpg")
    return frac_p


@pytest.mark.skipif(not DEFAULT_CKPT.is_file(), reason="Trained fracture checkpoint is missing; real inference is blocked")
def test_fracture_inference_engine_schema(sample_white_image: Path):
    """Verify FractureInferenceEngine outputs well-formed structured dictionary."""
    engine = FractureInferenceEngine(device="cpu")
    res = engine.predict(sample_white_image)

    assert res["task"] == "fracture"
    assert res["result"] in ["fracture", "no_fracture", "uncertain"]
    assert 0.0 <= res["fracture_probability"] <= 1.0
    assert 0.0 <= res["confidence"] <= 1.0
    assert "status_description" in res
    assert "thresholds" in res
    assert "decision" in res["thresholds"]
    assert "uncertainty_band" in res["thresholds"]


def test_stage4_pipeline_output_schema(sample_orange_image: Path, trained_checkpoints):
    """Verify Stage4InferencePipeline output schema matches specification."""
    pipeline = Stage4InferencePipeline(device="cpu")
    result = pipeline.predict(sample_orange_image)

    assert "xray_validation" in result
    assert "body_part" in result
    assert "abnormality" in result
    assert "models" in result
    assert "pipeline_status" in result
    assert "timings_ms" in result

    assert result["models"]["validator"] == "XRayValidatorCNN"
    assert result["models"]["body_part"] == "BodyPartClassifierCNN"
    assert result["models"]["fracture"] == "FractureClassifierCNN"


def test_stage4_pipeline_non_xray_gating(sample_orange_image: Path, trained_checkpoints):
    """Verify Gate 1: Non-radiograph input is rejected and does not reach abnormality classifier."""
    pipeline = Stage4InferencePipeline(device="cpu")
    result = pipeline.predict(sample_orange_image)

    # Orange synthetic image is rejected as NON_XRAY
    assert result["xray_validation"]["result"] == "non_xray"
    assert result["pipeline_status"] == "REJECTED_NON_XRAY"
    assert result["body_part"] is None
    assert result["abnormality"] is None
    assert "rejection_reason" in result


def test_stage4_pipeline_real_xray_routing(real_xray_image: Path, trained_checkpoints):
    """Verify Gate 2 & 3: Real radiograph routes through body part and abnormality classification."""
    pipeline = Stage4InferencePipeline(device="cpu")
    result = pipeline.predict(real_xray_image)

    assert result["xray_validation"]["result"] == "x_ray"
    assert result["body_part"] is not None
    assert result["body_part"]["result"] in pipeline.SUPPORTED_BODY_PARTS
    assert result["abnormality"] is not None
    assert result["abnormality"]["task"] == "fracture"
    assert result["abnormality"]["result"] in ["fracture", "no_fracture", "uncertain"]
    assert result["pipeline_status"] == "ANALYSIS_COMPLETE"
    assert "fracture_classifier_alone_ms" in result["timings_ms"]
    assert "total_pipeline_ms" in result["timings_ms"]


def test_stage4_pipeline_metadata(trained_checkpoints):
    """Verify get_metadata returns provenance, model hashes, and thresholds."""
    pipeline = Stage4InferencePipeline(device="cpu")
    meta = pipeline.get_metadata()

    assert "models" in meta
    models = meta["models"]
    assert "validator" in models
    assert "body_part" in models
    assert "fracture" in models

    assert "sha256" in models["fracture"]
    assert "decision_threshold" in models["fracture"]
    assert "uncertainty_band" in models["fracture"]


def test_medical_language_guardrails(real_xray_image: Path, trained_checkpoints):
    """Verify explanatory text conforms to patient reassurance guidelines without diagnostic diagnosis."""
    pipeline = Stage4InferencePipeline(device="cpu")
    result = pipeline.predict(real_xray_image)

    if result["abnormality"]:
        desc = result["abnormality"]["status_description"].lower()
        # Must not make definitive clinical claims
        assert "you have a fracture" not in desc
        assert "diagnosed" not in desc
        assert any(phrase in desc for phrase in ["features associated with", "no features", "indeterminate"])
