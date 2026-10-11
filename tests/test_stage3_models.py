"""Automated unit and integration tests for Stage 3 models."""

import pytest
import torch
from pathlib import Path

from ml.models.xray_validator import XRayValidatorCNN
from ml.models.body_part_classifier import BodyPartClassifierCNN
from ml.training.metrics import calculate_binary_metrics, calculate_multiclass_metrics
import numpy as np


def test_xray_validator_shapes():
    """Verify input/output shapes of Model A (X-Ray Validator)."""
    model = XRayValidatorCNN()
    model.eval()

    # Batch of 4 grayscale 224x224 images
    dummy_input = torch.randn(4, 1, 224, 224)
    logits = model(dummy_input)

    assert logits.shape == (4, 1), f"Expected shape (4, 1), got {logits.shape}"
    assert not torch.isnan(logits).any()


def test_body_part_classifier_shapes():
    """Verify input/output shapes of Model B (Body-Part Classifier)."""
    model = BodyPartClassifierCNN(num_classes=4)
    model.eval()

    # Batch of 3 grayscale 224x224 images
    dummy_input = torch.randn(3, 1, 224, 224)
    logits = model(dummy_input)

    assert logits.shape == (3, 4), f"Expected shape (3, 4), got {logits.shape}"
    assert not torch.isnan(logits).any()


def test_binary_metrics_calculation():
    """Verify calculation of binary evaluation metrics."""
    y_true = np.array([1, 1, 0, 0, 1])
    y_prob = np.array([0.9, 0.8, 0.1, 0.2, 0.7])

    metrics = calculate_binary_metrics(y_true, y_prob, threshold=0.5)

    assert metrics["accuracy"] == 1.0
    assert metrics["recall_sensitivity"] == 1.0
    assert metrics["specificity"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["roc_auc"] == 1.0


def test_multiclass_metrics_calculation():
    """Verify multiclass metrics calculation."""
    y_true = np.array([0, 1, 2, 3])
    # Mock probabilities where each matches ground truth
    y_prob = np.array([
        [0.8, 0.1, 0.05, 0.05],
        [0.1, 0.7, 0.1, 0.1],
        [0.05, 0.05, 0.8, 0.1],
        [0.1, 0.1, 0.1, 0.7],
    ])
    class_names = ["hand", "leg", "hip", "shoulder"]

    metrics = calculate_multiclass_metrics(y_true, y_prob, class_names=class_names)

    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert len(metrics["per_class"]) == 4
