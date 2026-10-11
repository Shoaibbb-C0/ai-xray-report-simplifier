"""Integration test for Stage 3 inference pipeline and CLI."""

from pathlib import Path
import pytest
from PIL import Image

from ml.inference.stage3_pipeline import Stage3InferencePipeline


def test_stage3_pipeline_execution(tmp_path: Path):
    pipeline = Stage3InferencePipeline(device="cpu")

    # Test synthetic pure white non-xray image
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    temp_img_path = tmp_path / "white.png"
    img.save(temp_img_path)

    result = pipeline.predict(temp_img_path)

    assert "validator" in result
    assert result["validator"]["decision"] in ["X_RAY", "NON_XRAY", "UNCERTAIN"]
    assert "pipeline_status" in result


def test_stage3_pipeline_metadata():
    pipeline = Stage3InferencePipeline(device="cpu")
    meta = pipeline.get_metadata()

    assert "validator" in meta
    assert "body_part" in meta
    assert meta["validator"]["thresholds"]["lower"] == 0.35
    assert meta["validator"]["thresholds"]["upper"] == 0.65
    assert meta["body_part"]["unknown_threshold"] == 0.60
