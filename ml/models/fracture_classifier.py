"""PyTorch Neural Network Architecture for Model C: Fracture Classifier.

Designed for bone fracture detection on musculoskeletal radiographs (FracAtlas dataset).
Custom CNN trained from scratch on 224x224 grayscale radiographs.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class FractureClassifierCNN(nn.Module):
    """Custom Convolutional Neural Network for binary fracture abnormality classification.
    
    Architecture:
    Input: [B, 1, 224, 224] grayscale radiograph
    Block 1: Conv(1->32, 3x3) -> BatchNorm -> ReLU -> MaxPool(2)  [112x112]
    Block 2: Conv(32->64, 3x3) -> BatchNorm -> ReLU -> MaxPool(2)  [56x56]
    Block 3: Conv(64->128, 3x3) -> BatchNorm -> ReLU -> MaxPool(2) [28x28]
    Block 4: Conv(128->256, 3x3) -> BatchNorm -> ReLU -> MaxPool(2) [14x14]
    Block 5: Conv(256->256, 3x3) -> BatchNorm -> ReLU -> MaxPool(2) [7x7]
    Head: AdaptiveAvgPool(1x1) -> Flatten -> Dropout(0.4) -> Linear(256->64) -> ReLU -> Dropout(0.2) -> Linear(64->1)
    Output: Logits [B, 1] for binary BCEWithLogitsLoss (Positive = Fracture, Negative = No Fracture)
    """

    TASK_NAME = "fracture"
    CLASSES = ["no_fracture", "fracture"]

    def __init__(self, dropout_rate: float = 0.4) -> None:
        super().__init__()

        self.block1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.block4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.block5 = nn.Sequential(
            nn.Conv2d(256, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.pool = nn.AdaptiveAvgPool2d((1, 1))

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.5),
            nn.Linear(64, 1),
        )

    def get_last_conv_layer(self) -> nn.Module:
        """Returns the last convolutional layer for Grad-CAM inspection."""
        return self.block5[0]

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract spatial feature map before pooling."""
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.block5(x)
        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass emitting binary logit."""
        feats = self.forward_features(x)
        pooled = self.pool(feats)
        logits = self.classifier(pooled)
        return logits
