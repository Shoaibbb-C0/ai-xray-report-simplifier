"""Training script for Model A: X-Ray Validator.

Trains XRayValidatorCNN on balanced binary dataset (X-Ray vs Non-X-Ray).
Uses BCEWithLogitsLoss, AdamW optimizer, and validates each epoch.
Saves the best checkpoint to ml/saved_models/stage3/validator/best_validator.pt.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import torch
import torch.nn as nn
from PIL import ImageFile

from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.torch_dataset import NormalizedXRayDataset, create_xray_dataloader
from ml.models.xray_validator import XRayValidatorCNN
from ml.preprocessing.pipeline import XRayPreprocessor
from ml.training.engine import TrainingEngine

# Safety for truncated raw images
ImageFile.LOAD_TRUNCATED_IMAGES = True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_validator")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPLITS_DIR = PROJECT_ROOT / "ml" / "datasets" / "splits" / "validator"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "saved_models" / "stage3" / "validator"


def load_normalized_samples(json_path: Path) -> List[NormalizedSample]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [NormalizedSample(**item) for item in data]


def train_validator(
    epochs: int = 5,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-4,
    device_str: str = "cpu",
) -> Dict[str, Any]:
    """Train Model A (X-Ray Validator)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device(device_str)

    preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)

    train_manifest = SPLITS_DIR / "train.json"
    val_manifest = SPLITS_DIR / "validation.json"

    logger.info("Loading training manifest: %s", train_manifest)
    train_samples = load_normalized_samples(train_manifest)
    logger.info("Loading validation manifest: %s", val_manifest)
    val_samples = load_normalized_samples(val_manifest)

    train_dataset = NormalizedXRayDataset(train_samples, preprocessor=preprocessor, task="binary")
    val_dataset = NormalizedXRayDataset(val_samples, preprocessor=preprocessor, task="binary")

    train_loader = create_xray_dataloader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = create_xray_dataloader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    logger.info("Train dataset size: %d | Val dataset size: %d", len(train_dataset), len(val_dataset))

    torch.manual_seed(42)
    model = XRayValidatorCNN().to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    checkpoint_path = OUTPUT_DIR / "best_validator.pt"

    engine = TrainingEngine(
        model=model,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
    )

    logger.info("Starting training of XRayValidatorCNN for %d epochs...", epochs)
    fit_summary = engine.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=epochs,
        checkpoint_path=checkpoint_path,
        task_type="binary",
        primary_metric="balanced_accuracy",
        patience=3,
        extra_meta={
            "model_name": "XRayValidatorCNN",
            "in_channels": 1,
            "input_resolution": [224, 224],
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
            "hyperparameters": {
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "weight_decay": weight_decay,
                "optimizer": "AdamW",
                "loss": "BCEWithLogitsLoss",
            },
        },
    )

    # Save training history
    history_file = OUTPUT_DIR / "history.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(fit_summary, f, indent=2)

    logger.info("Training history written to %s", history_file)
    logger.info("Best checkpoint saved at %s", checkpoint_path)
    return fit_summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train X-Ray Validator CNN")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    args = parser.parse_args()

    train_validator(epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr)
