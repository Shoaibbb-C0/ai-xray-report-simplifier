# Inference Engine

## Purpose
Provides the runtime interface for loading serialized model checkpoints and performing forward-pass evaluations on new incoming radiographs.

## Architecture
- Loads state dicts into lightweight PyTorch evaluation mode (`model.eval()`, `torch.no_grad()`).
- Applies validation preprocessing transformations consistently with the training pipeline.
- Translates raw logits into calibrated probability scores.
- Feeds outputs directly to the FastAPI backend service layer.
