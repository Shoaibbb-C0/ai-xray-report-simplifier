"""Tests for radiograph image preprocessing and letterboxing."""

import numpy as np
import pytest
import torch
from PIL import Image

from ml.preprocessing.pipeline import XRayPreprocessor


@pytest.fixture
def synthetic_rectangular_image(tmp_path):
    """Fixture providing a synthetic wide rectangular test image."""
    img_path = tmp_path / "test_rect.png"
    # Create 400x200 RGB image with gradient
    arr = np.zeros((200, 400, 3), dtype=np.uint8)
    arr[:, :, 0] = 128
    arr[:, :, 1] = 200
    img = Image.fromarray(arr)
    img.save(img_path)
    return img_path


def test_preprocessor_output_shape_and_dtype(synthetic_rectangular_image):
    """Verify preprocessor produces [1, 224, 224] float32 tensor."""
    preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)
    tensor = preprocessor(synthetic_rectangular_image)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 224, 224)
    assert tensor.dtype == torch.float32
    assert not torch.isnan(tensor).any()
    assert not torch.isinf(tensor).any()


def test_letterboxing_preserves_aspect_ratio(synthetic_rectangular_image):
    """Verify letterboxing zero-pads border while maintaining aspect ratio."""
    preprocessor = XRayPreprocessor(target_size=(224, 224))
    img = Image.open(synthetic_rectangular_image).convert("L")
    letterboxed = preprocessor.letterbox_image(img)

    assert letterboxed.size == (224, 224)
    arr = np.array(letterboxed)

    # Since input is wide (400x200), aspect ratio is 2:1.
    # Scaled to width 224 -> height is 112.
    # Top and bottom padding should each be (224 - 112) // 2 = 56 pixels of zero.
    assert (arr[0:50, :] == 0).all()   # Top pad
    assert (arr[174:, :] == 0).all()   # Bottom pad
    assert (arr[56:168, :] > 0).any()  # Active content area


def test_normalization_values():
    """Verify channel normalization formula (x - mean) / std."""
    preprocessor = XRayPreprocessor(target_size=(10, 10), mean=0.5, std=0.5)
    # Uniform black image (0 intensity) -> (0 - 0.5) / 0.5 = -1.0
    black_img = Image.new("L", (10, 10), 0)
    tensor_black = preprocessor(black_img)
    assert pytest.approx(tensor_black.min().item(), 1e-4) == -1.0
    assert pytest.approx(tensor_black.max().item(), 1e-4) == -1.0

    # Uniform white image (255 intensity) -> (1.0 - 0.5) / 0.5 = 1.0
    white_img = Image.new("L", (10, 10), 255)
    tensor_white = preprocessor(white_img)
    assert pytest.approx(tensor_white.min().item(), 1e-4) == 1.0
    assert pytest.approx(tensor_white.max().item(), 1e-4) == 1.0
