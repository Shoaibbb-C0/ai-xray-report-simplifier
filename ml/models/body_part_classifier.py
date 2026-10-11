"""PyTorch Neural Network Architecture for Model B: Body-Part Classifier."""

import torch
import torch.nn as nn


class BodyPartClassifierCNN(nn.Module):
    """Custom from-scratch Convolutional Neural Network for 4-class anatomical classification.
    
    Classes: HAND (0), LEG (1), HIP (2), SHOULDER (3)
    
    Architecture:
    Input: [B, 1, 224, 224] grayscale radiograph
    Block 1: Conv(1->16, 3x3) -> BatchNorm -> ReLU -> MaxPool(2) [112x112]
    Block 2: Conv(16->32, 3x3) -> BatchNorm -> ReLU -> MaxPool(2) [56x56]
    Block 3: Conv(32->64, 3x3) -> BatchNorm -> ReLU -> MaxPool(2) [28x28]
    Block 4: Conv(64->128, 3x3) -> BatchNorm -> ReLU -> MaxPool(2) [14x14]
    Head: AdaptiveAvgPool(1x1) -> Flatten -> Dropout(0.4) -> Linear(128->64) -> ReLU -> Linear(64->4)
    Output: Logits [B, 4] for CrossEntropyLoss
    """

    CLASS_NAMES = ["hand", "leg", "hip", "shoulder"]

    def __init__(self, num_classes: int = 4, dropout_rate: float = 0.4) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(1, 16, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 2
            nn.Conv2d(16, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 3
            nn.Conv2d(32, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 4
            nn.Conv2d(64, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass emitting class logits [B, num_classes]."""
        feats = self.features(x)
        pooled = self.pool(feats)
        logits = self.classifier(pooled)
        return logits

    def count_parameters(self) -> int:
        """Returns total trainable parameter count."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
