# Training Pipeline

## Purpose
Contains training orchestrations, loss definitions, and model architectures built natively in PyTorch.

## Responsibilities
- Model architecture definitions (CNN backbones, attention heads, body part classifiers).
- Multi-label loss formulations (e.g. weighted BCEWithLogitsLoss for class imbalances).
- Training epoch loops, learning rate scheduling, and early stopping checkpoints.
- Model serialization to `ml/saved_models/`.
