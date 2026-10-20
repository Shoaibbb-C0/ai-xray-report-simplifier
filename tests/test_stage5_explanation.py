"""Automated test suite for Stage 5 Visual Explanation Engine.

Verifies schema compliance, deterministic patient-safe language, visual asset mapping,
Grad-CAM attention safety gating, localization boundary enforcement, and regression safety.
"""

from pathlib import Path
import json
import pytest
import torch

from ml.explanation.schema import (
    AnalysisStatus,
    BodyPartId,
    ExplanationResult,
    FindingState,
)
from ml.explanation.engine import VisualExplanationEngine
from ml.explanation.visual_mapper import resolve_illustration
from ml.explanation.glossary import get_glossary
from ml.explanation.translations import TRANSLATION_REGISTRY, t
from ml.inference.fracture_classifier import DEFAULT_CKPT


@pytest.fixture
def engine() -> VisualExplanationEngine:
    return VisualExplanationEngine(device="cpu")


@pytest.fixture
def sample_hand_fracture_cascade():
    return {
        "xray_validation": {"is_xray": True, "confidence": 0.99},
        "body_part": {"predicted_class": "HAND", "confidence": 0.94},
        "abnormality": {"result": "fracture", "fracture_probability": 0.84, "confidence": 0.84},
        "pipeline_status": "ANALYSIS_COMPLETE",
        "models": {
            "validator": "ValidatorCNN_Stage3",
            "body_part": "BodyPartClassifierCNN_Stage3",
            "fracture_classifier": "FractureClassifierCNN_Stage4",
        },
    }


@pytest.fixture
def sample_leg_no_fracture_cascade():
    return {
        "xray_validation": {"is_xray": True, "confidence": 0.98},
        "body_part": {"predicted_class": "LEG", "confidence": 0.91},
        "abnormality": {"result": "no_fracture", "fracture_probability": 0.12, "confidence": 0.88},
        "pipeline_status": "ANALYSIS_COMPLETE",
    }


@pytest.fixture
def sample_uncertain_cascade():
    return {
        "xray_validation": {"is_xray": True, "confidence": 0.97},
        "body_part": {"predicted_class": "SHOULDER", "confidence": 0.89},
        "abnormality": {"result": "uncertain", "fracture_probability": 0.35, "confidence": 0.35},
        "pipeline_status": "ANALYSIS_COMPLETE",
    }


@pytest.fixture
def sample_non_xray_cascade():
    return {
        "xray_validation": {"is_xray": False, "confidence": 0.05},
        "body_part": {"predicted_class": "UNKNOWN", "confidence": 0.20},
        "abnormality": None,
        "pipeline_status": "REJECTED_NON_XRAY",
    }


@pytest.fixture
def sample_unknown_body_part_cascade():
    return {
        "xray_validation": {"is_xray": True, "confidence": 0.95},
        "body_part": {"predicted_class": "UNKNOWN", "confidence": 0.30},
        "abnormality": None,
        "pipeline_status": "REJECTED_UNKNOWN_ANATOMY",
    }


def test_fracture_suspected_explanation(engine, sample_hand_fracture_cascade):
    """Verify fracture suspected state produces accurate schema and non-diagnostic phrasing."""
    res: ExplanationResult = engine.explain(sample_hand_fracture_cascade)

    assert res.analysis_status == AnalysisStatus.VALID_XRAY_FRACTURE_SUSPECTED
    assert res.finding.state == FindingState.SUSPECTED
    assert res.body_part.id == BodyPartId.HAND
    assert "may be associated with a fracture" in res.summary
    assert res.visual.educational_only is True
    assert res.visual.exact_location is False
    assert Path(res.visual.illustration_path).exists()


def test_no_fracture_signal_explanation(engine, sample_leg_no_fracture_cascade):
    """Verify negative prediction includes mandatory clinical clarification."""
    res: ExplanationResult = engine.explain(sample_leg_no_fracture_cascade)

    assert res.analysis_status == AnalysisStatus.VALID_XRAY_NO_FRACTURE_SIGNAL
    assert res.finding.state == FindingState.NO_SIGNAL
    assert "did not detect strong fracture-related features" in res.summary
    assert "does not rule out a fracture" in res.what_the_result_means
    assert Path(res.visual.illustration_path).exists()


def test_uncertain_state_explanation(engine, sample_uncertain_cascade):
    """Verify uncertain predictions explain low confidence and suppress Grad-CAM attention."""
    res: ExplanationResult = engine.explain(sample_uncertain_cascade, generate_attention=True)

    assert res.analysis_status == AnalysisStatus.VALID_XRAY_UNCERTAIN
    assert res.finding.state == FindingState.UNCERTAIN
    assert "could not make a confident classification" in res.summary
    assert res.attention.available is False
    assert Path(res.visual.illustration_path).exists()


def test_non_xray_validation_rejection(engine, sample_non_xray_cascade):
    """Verify non-X-ray inputs route to safe rejection without running fracture models."""
    res: ExplanationResult = engine.explain(sample_non_xray_cascade)

    assert res.analysis_status == AnalysisStatus.NON_XRAY
    assert res.finding.state == FindingState.NOT_ANALYZED
    assert "model did not accept" in res.summary
    assert res.translation_keys["purpose_key"] == "validation.purpose"
    assert res.attention.available is False
    assert res.visual.illustration_id == "common_non_xray"
    assert Path(res.visual.illustration_path).exists()


def test_unknown_body_part_explanation(engine, sample_unknown_body_part_cascade):
    """Verify unrecognized body anatomy is flagged as unsupported."""
    res: ExplanationResult = engine.explain(sample_unknown_body_part_cascade)

    assert res.analysis_status == AnalysisStatus.BODY_PART_UNKNOWN
    assert "could not confidently" in res.summary
    assert "strictly calibrated" not in res.what_the_result_means
    assert res.body_part.id == BodyPartId.UNKNOWN
    assert res.finding.state == FindingState.UNSUPPORTED
    assert "outside the currently supported regions" not in res.summary
    assert res.attention.available is False


def test_model_unavailable_state(engine):
    """Verify graceful handling when abnormality model is offline."""
    cascade = {
        "xray_validation": {"is_xray": True, "confidence": 0.99},
        "body_part": {"predicted_class": "HAND", "confidence": 0.95},
        "abnormality": None,
        "pipeline_status": "MODEL_UNAVAILABLE",
    }
    res = engine.explain(cascade)

    assert res.analysis_status == AnalysisStatus.MODEL_UNAVAILABLE
    assert "offline or unavailable" in res.summary
    assert res.attention.available is False


def test_all_visual_assets_exist_on_disk():
    """Verify that every supported anatomy and finding combination resolves to an existing SVG file."""
    body_parts = [BodyPartId.HAND, BodyPartId.LEG, BodyPartId.HIP, BodyPartId.SHOULDER, BodyPartId.MIXED, BodyPartId.UNKNOWN]
    finding_states = [FindingState.SUSPECTED, FindingState.NO_SIGNAL, FindingState.UNCERTAIN]

    for bp in body_parts:
        for fs in finding_states:
            visual = resolve_illustration(bp, fs)
            svg_path = Path(visual.illustration_path)
            assert svg_path.exists(), f"Missing visual asset file: {svg_path}"
            assert visual.educational_only is True
            assert visual.exact_location is False

            # Check public frontend mirror exists as well
            frontend_path = Path("frontend/public") / visual.illustration_path
            assert frontend_path.exists(), f"Missing frontend asset mirror: {frontend_path}"


def test_svg_accessibility_and_safety():
    """Verify SVG assets include accessible titles, descriptions, and non-diagnostic notices."""
    svg_dir = Path("assets/anatomy")
    svg_files = list(svg_dir.rglob("*.svg"))
    assert len(svg_files) >= 10, f"Expected at least 10 SVG files, found {len(svg_files)}"

    for f in svg_files:
        content = f.read_text(encoding="utf-8")
        assert "<title>" in content, f"SVG {f.name} missing <title>"
        assert "<desc>" in content, f"SVG {f.name} missing <desc>"
        assert 'role="img"' in content, f"SVG {f.name} missing role='img'"

        if "fracture" in f.name:
            assert "Example illustration" in content or "generic" in content.lower(), (
                f"Fracture SVG {f.name} missing mandatory educational indicator"
            )


def test_localization_boundary_strictly_disabled(engine, sample_hand_fracture_cascade):
    """Verify experimental localization head is NOT exposed to patient-facing output."""
    res = engine.explain(sample_hand_fracture_cascade)
    assert res.localization.available is False
    assert res.localization.exact_location is False
    assert res.localization.status == "experimental_unverified"


def test_json_serialization_compatibility(engine, sample_hand_fracture_cascade):
    """Verify explanation output serializes cleanly to JSON for future Supabase storage."""
    res = engine.explain(sample_hand_fracture_cascade)
    dumped_dict = res.model_dump()
    json_str = res.model_dump_json()

    assert isinstance(dumped_dict, dict)
    assert isinstance(json_str, str)
    reloaded = json.loads(json_str)
    assert reloaded["analysis_status"] == "VALID_XRAY_FRACTURE_SUSPECTED"
    assert reloaded["body_part"]["id"] == "hand"


def test_multilingual_translation_keys(engine, sample_hand_fracture_cascade):
    """Verify localization support for English, Hindi, and Marathi."""
    for lang in ["en", "hi", "mr"]:
        res = engine.explain(sample_hand_fracture_cascade, lang=lang)
        assert res.summary is not None
        assert len(res.summary) > 0
        assert res.language == lang


def test_critical_translations_do_not_fall_back_to_english():
    for language in ("hi", "mr"):
        assert set(TRANSLATION_REGISTRY["en"]).issubset(TRANSLATION_REGISTRY[language])


def test_explanation_respects_explicit_validation_policy(engine, sample_hand_fracture_cascade):
    sample_hand_fracture_cascade["xray_validation"] = {"result":"x_ray", "confidence":.55, "probability":.55}
    result = engine.explain(sample_hand_fracture_cascade)
    assert result.analysis_status == AnalysisStatus.VALID_XRAY_FRACTURE_SUSPECTED


@pytest.mark.parametrize("source_size,overlay_size", [((64,64),(64,64)), ((400,800),(64,128))])
def test_attention_aligns_with_original_image_without_model_padding(engine, monkeypatch, source_size, overlay_size):
    import base64
    import io
    import numpy as np
    from PIL import Image
    class Attention:
        def generate_heatmap(self, tensor):
            return np.ones((128,128), dtype=np.float32)
    engine.attention_size = (128,128)
    monkeypatch.setattr(engine, "_get_gradcam", lambda: Attention())
    with Image.new("RGB", source_size) as source:
        encoded = engine.generate_attention_overlay(source)
    with Image.open(io.BytesIO(base64.b64decode(encoded.split(",",1)[1]))) as overlay:
        assert overlay.size == overlay_size


def test_safety_regression_forbidden_medical_claims(engine):
    """Regression test: Ensure patient-facing text NEVER contains dangerous or overconfident claims."""
    forbidden_affirmative_phrases = [
        "you have a fracture",
        "you definitely have",
        "confirmed fracture",
        "no fracture exists",
        "your exact fracture location",
        "this is the exact fracture location",
        "clinically validated",
        "strictly calibrated",
        "100% accurate",
        "guaranteed",
        "definitive diagnosis",
    ]

    cascades = [
        {"xray_validation": {"is_xray": True, "confidence": 0.99}, "body_part": {"predicted_class": "HAND", "confidence": 0.95}, "abnormality": {"result": "fracture", "fracture_probability": 0.99, "confidence": 0.99}},
        {"xray_validation": {"is_xray": True, "confidence": 0.99}, "body_part": {"predicted_class": "LEG", "confidence": 0.95}, "abnormality": {"result": "no_fracture", "fracture_probability": 0.01, "confidence": 0.99}},
        {"xray_validation": {"is_xray": True, "confidence": 0.99}, "body_part": {"predicted_class": "HIP", "confidence": 0.95}, "abnormality": {"result": "uncertain", "fracture_probability": 0.35, "confidence": 0.35}},
        {"xray_validation": {"is_xray": False, "confidence": 0.01}, "body_part": {"predicted_class": "UNKNOWN", "confidence": 0.0}, "abnormality": None},
    ]

    for cascade in cascades:
        res = engine.explain(cascade)
        all_text = f"{res.summary} {res.what_this_test_checks} {res.what_the_result_means} {res.next_step_message} {' '.join(res.limitations)}".lower()

        for phrase in forbidden_affirmative_phrases:
            assert phrase not in all_text, f"Forbidden affirmative phrase '{phrase}' found in patient explanation!"


@pytest.mark.skipif(
    not DEFAULT_CKPT.is_file(),
    reason="Trained fracture checkpoint is missing; real Grad-CAM is blocked",
)
def test_gradcam_execution_with_real_xray(engine, sample_hand_fracture_cascade):
    """Verify Grad-CAM executes and generates transparent thermal overlay for positive prediction."""
    from ml.datasets.registry import RAW_DATASETS_DIR
    from ml.datasets.adapters.fracatlas import FracAtlasAdapter
    rows = FracAtlasAdapter(RAW_DATASETS_DIR / "fracatlas").load_manifest()
    sample = next((row for row in rows if row.body_part == "hand" and row.is_abnormal), None)
    if sample is None:
        pytest.skip("A local FracAtlas hand radiograph is required")
    sample_img = Path(sample.image_path)
    if not sample_img.is_file():
        pytest.skip("Local sample radiograph is missing")
    if sample_img.exists():
        res = engine.explain(sample_hand_fracture_cascade, image_input=sample_img, generate_attention=True)
        assert res.attention.available is True
        assert res.attention.overlay_base64.startswith("data:image/png;base64,")
        assert res.attention.is_exact_localization is False
        assert res.attention.clinical_localization is False
