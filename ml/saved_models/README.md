# Saved Models

## Storage of Trained Weights
This directory stores serialized PyTorch model weights (`.pth`, `.pt`) produced during training.

## Git Rules
- Model binaries (`*.pth`, `*.pt`, `*.bin`, `*.onnx`) are **strictly excluded** from version control via `.gitignore`.
- Model metadata files or training summaries (e.g., JSON descriptions of architecture configurations) can be tracked alongside version tags.
- In Stage 1, no models have been trained and no placeholder binary files exist.
