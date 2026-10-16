"""Lightweight experimental fracture localization model for single-region bounding-box regression.

IMPORTANT & LIMITATION NOTICE:
This is an EXPERIMENTAL model strictly evaluated on the single-box fracture subset.
In images with multiple fractures (171 cases in FracAtlas), single-box regression cannot
detect secondary or tertiary lesions. It is NOT a production radiological lesion detector.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from typing import Tuple

from ml.models.fracture_classifier import FractureClassifierCNN


class SingleBoxLocalizationHead(nn.Module):
    """Lightweight regression head predicting [xmin, ymin, xmax, ymax] in [0.0, 1.0]."""

    def __init__(self, in_channels: int = 256) -> None:
        super().__init__()
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_channels, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 4),
            nn.Sigmoid(),  # Bound coordinates to [0.0, 1.0]
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Predicts normalized bounding box [B, 4] where coords are (xmin, ymin, xmax, ymax)."""
        pooled = self.pool(features)
        coords = self.regressor(pooled)
        return coords


def compute_iou(box1: torch.Tensor, box2: torch.Tensor) -> torch.Tensor:
    """Computes Intersection-over-Union (IoU) between two batches of boxes [B, 4]."""
    x1 = torch.max(box1[:, 0], box2[:, 0])
    y1 = torch.max(box1[:, 1], box2[:, 1])
    x2 = torch.min(box1[:, 2], box2[:, 2])
    y2 = torch.min(box1[:, 3], box2[:, 3])

    inter_w = torch.clamp(x2 - x1, min=0.0)
    inter_h = torch.clamp(y2 - y1, min=0.0)
    intersection = inter_w * inter_h

    area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
    area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])
    union = area1 + area2 - intersection

    iou = torch.where(union > 0, intersection / union, torch.zeros_like(union))
    return iou
