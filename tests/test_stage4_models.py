"""Automated unit and regression tests for Stage 4 Model C (Fracture Classifier) and components."""

from pathlib import Path
import tempfile
import numpy as np
import pytest
import torch
import torch.nn as nn

from ml.datasets.localization import BoundingBox, parse_pascal_voc_xml
from ml.evaluation.gradcam import FractureGradCAM
from ml.evaluation.threshold_analysis import run_threshold_grid_search, select_calibrated_thresholds
from ml.models.fracture_classifier import FractureClassifierCNN
from ml.models.localization_head import SingleBoxLocalizationHead, compute_iou
from ml.training.metrics import calculate_binary_metrics


def test_fracture_classifier_shapes():
    """Verify input/output shapes of Model C (Fracture Classifier)."""
    model = FractureClassifierCNN(dropout_rate=0.4)
    model.eval()

    dummy_input = torch.randn(4, 1, 224, 224)
    logits = model(dummy_input)

    assert logits.shape == (4, 1), f"Expected shape (4, 1), got {logits.shape}"
    assert not torch.isnan(logits).any(), "Found NaN in output logits"
    assert not torch.isinf(logits).any(), "Found Inf in output logits"


def test_fracture_classifier_loss_and_gradients():
    """Verify loss calculation and backpropagation compatibility."""
    model = FractureClassifierCNN()
    model.train()

    dummy_input = torch.randn(2, 1, 224, 224)
    dummy_target = torch.tensor([[1.0], [0.0]], dtype=torch.float32)

    criterion = nn.BCEWithLogitsLoss()
    logits = model(dummy_input)
    loss = criterion(logits, dummy_target)

    loss.backward()

    # Ensure gradients propagated to first convolution layer
    first_conv = model.block1[0]
    assert first_conv.weight.grad is not None
    assert not torch.isnan(first_conv.weight.grad).any()


def test_class_weighting_loss():
    """Verify weighted BCE penalizes false negatives proportionally to pos_weight."""
    pos_weight = torch.tensor([4.811])
    criterion_weighted = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    criterion_unweighted = nn.BCEWithLogitsLoss()

    # Model incorrectly predicts negative (large negative logit) for positive ground truth
    logits = torch.tensor([[-2.0]], dtype=torch.float32)
    target = torch.tensor([[1.0]], dtype=torch.float32)

    loss_weighted = criterion_weighted(logits, target).item()
    loss_unweighted = criterion_unweighted(logits, target).item()

    assert loss_weighted > loss_unweighted * 3.5, "Weighted loss must heavily penalize false negatives"


def test_binary_metrics_calculation():
    """Verify calculation of accuracy, balanced accuracy, sensitivity, specificity, and F1."""
    y_true = np.array([1, 1, 0, 0, 1, 0])
    y_prob = np.array([0.9, 0.8, 0.1, 0.2, 0.7, 0.4])

    metrics = calculate_binary_metrics(y_true, y_prob, threshold=0.5)

    assert metrics["accuracy"] == 1.0
    assert metrics["recall_sensitivity"] == 1.0
    assert metrics["specificity"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["roc_auc"] == 1.0
    assert metrics["pr_auc"] == 1.0
    assert metrics["false_negatives"] == 0
    assert metrics["false_positives"] == 0


def test_threshold_grid_search_and_calibration():
    """Verify threshold analysis and uncertainty calibration logic."""
    y_true = np.array([1, 1, 1, 0, 0, 0, 0, 0])
    y_prob = np.array([0.85, 0.75, 0.40, 0.10, 0.15, 0.20, 0.30, 0.45])

    grid = run_threshold_grid_search(y_true, y_prob, start=0.2, end=0.8, step=0.1)
    assert len(grid) > 0

    policy = select_calibrated_thresholds(grid, y_prob)
    assert "decision_threshold" in policy
    assert "uncertainty_policy" in policy
    u_pol = policy["uncertainty_policy"]
    assert u_pol["lower_bound"] < u_pol["upper_bound"]


def test_checkpoint_save_and_load(tmp_path: Path):
    """Verify state_dict checkpoint serialization and restoration."""
    model_orig = FractureClassifierCNN()
    model_orig.eval()

    ckpt_path = tmp_path / "test_fracture.pt"
    torch.save({"model_state_dict": model_orig.state_dict(), "epoch": 1}, ckpt_path)

    model_loaded = FractureClassifierCNN()
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model_loaded.load_state_dict(ckpt["model_state_dict"])
    model_loaded.eval()

    x = torch.randn(2, 1, 224, 224)
    with torch.no_grad():
        out_orig = model_orig(x)
        out_loaded = model_loaded(x)

    torch.testing.assert_close(out_orig, out_loaded)


def test_corrupted_checkpoint_failure(tmp_path: Path):
    """Verify attempting to load corrupted checkpoint raises an error."""
    corrupt_file = tmp_path / "corrupted.pt"
    corrupt_file.write_bytes(b"garbage_non_torch_data_123456")

    with pytest.raises(Exception):
        torch.load(corrupt_file, map_location="cpu")


def test_gradcam_heatmap_generation():
    """Verify FractureGradCAM produces valid 2D normalized attention maps."""
    model = FractureClassifierCNN()
    model.eval()

    gradcam = FractureGradCAM(model)
    dummy_input = torch.randn(1, 1, 224, 224)

    cam = gradcam.generate_heatmap(dummy_input)
    gradcam.remove_hooks()

    assert cam.shape == (224, 224), f"Expected (224, 224), got {cam.shape}"
    assert cam.min() >= 0.0
    assert cam.max() <= 1.0


def test_bounding_box_geometry():
    """Verify BoundingBox geometry, area, validity, and letterboxing."""
    b_valid = BoundingBox(xmin=10, ymin=20, xmax=50, ymax=80)
    assert b_valid.is_valid()
    assert b_valid.width == 40
    assert b_valid.height == 60
    assert b_valid.area == 2400

    b_invalid = BoundingBox(xmin=50, ymin=80, xmax=10, ymax=20)
    assert not b_invalid.is_valid()

    # Normalized coords for 100x100 image
    norm = b_valid.to_normalized(img_w=100, img_h=100)
    assert norm == (0.1, 0.2, 0.5, 0.8)

    # Letterboxing to 224x224
    lb = b_valid.to_letterbox_224(orig_w=100, orig_h=100, target_size=224)
    assert lb[0] < lb[2]
    assert lb[1] < lb[3]


def test_localization_iou_calculation():
    """Verify IoU calculation on identical and disjoint boxes."""
    # Two identical boxes: IoU must be 1.0
    box_a = torch.tensor([[0.1, 0.1, 0.5, 0.5]])
    box_b = torch.tensor([[0.1, 0.1, 0.5, 0.5]])
    iou_identical = compute_iou(box_a, box_b)
    assert torch.isclose(iou_identical, torch.tensor([1.0]))

    # Disjoint boxes: IoU must be 0.0
    box_disjoint = torch.tensor([[0.6, 0.6, 0.9, 0.9]])
    iou_disjoint = compute_iou(box_a, box_disjoint)
    assert torch.isclose(iou_disjoint, torch.tensor([0.0]))
