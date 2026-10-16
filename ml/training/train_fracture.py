"""Training script for Model C: Fracture Classifier.

Trains FractureClassifierCNN on the leakage-safe FracAtlas v2 dataset.
- Uses weighted BCEWithLogitsLoss to handle class imbalance (pos_weight from train set).
- Applies conservative X-ray-safe data augmentation exclusively on training data.
- Employs AdamW optimizer and validation-based early stopping on validation F1 score.
- Saves the best checkpoint and tracked metadata to ml/saved_models/stage4/fracture_classifier/.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import ImageFile

from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.torch_dataset import NormalizedXRayDataset, create_xray_dataloader
from ml.models.fracture_classifier import FractureClassifierCNN
from ml.preprocessing.pipeline import XRayPreprocessor
from ml.training.engine import TrainingEngine

ImageFile.LOAD_TRUNCATED_IMAGES = True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_fracture")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPLITS_DIR = PROJECT_ROOT / "ml" / "datasets" / "splits" / "fracatlas_v2"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "saved_models" / "stage4" / "fracture_classifier"


def load_normalized_samples(json_path: Path) -> List[NormalizedSample]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [NormalizedSample.from_dict(item) for item in data]


def get_conservative_training_augmentation() -> transforms.Compose:
    """Returns conservative data augmentation preserving anatomical and radiograph validity."""
    return transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomAffine(
            degrees=(-8, 8),
            translate=(0.04, 0.04),
            scale=(0.96, 1.04),
            interpolation=transforms.InterpolationMode.BILINEAR,
        ),
    ])


def train_fracture_classifier(
    epochs: int = 8,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-4,
    device_str: str = "cpu",
    seed: int = 42,
    patience: int = 4,
) -> Dict[str, Any]:
    """Train Model C (Fracture Classifier CNN)."""
    torch.manual_seed(seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device(device_str)

    start_time = time.time()

    preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)
    train_aug = get_conservative_training_augmentation()

    train_manifest = SPLITS_DIR / "train.json"
    val_manifest = SPLITS_DIR / "validation.json"

    logger.info("Loading training manifest: %s", train_manifest)
    train_samples = load_normalized_samples(train_manifest)
    logger.info("Loading validation manifest: %s", val_manifest)
    val_samples = load_normalized_samples(val_manifest)

    # Calculate class imbalance weights strictly from training data
    n_pos = sum(1 for s in train_samples if s.is_abnormal)
    n_neg = len(train_samples) - n_pos
    pos_weight_value = round(n_neg / n_pos, 4) if n_pos > 0 else 1.0
    logger.info("Training distribution: %d negative, %d positive (pos_weight: %.4f)", n_neg, n_pos, pos_weight_value)

    torch.set_num_threads(min(8, torch.get_num_threads()))

    train_dataset = NormalizedXRayDataset(
        train_samples,
        preprocessor=preprocessor,
        task="binary",
        transform=train_aug,
        cache_tensors=True,
    )
    val_dataset = NormalizedXRayDataset(
        val_samples,
        preprocessor=preprocessor,
        task="binary",
        transform=None,  # Untouched validation
        cache_tensors=True,
    )

    train_loader = create_xray_dataloader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = create_xray_dataloader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    logger.info("Train dataset size: %d | Val dataset size: %d", len(train_dataset), len(val_dataset))

    model = FractureClassifierCNN().to(device)
    param_count = sum(p.numel() for p in model.parameters())
    logger.info("Instantiated FractureClassifierCNN with %d parameters", param_count)

    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight_value], device=device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

    checkpoint_path = OUTPUT_DIR / "best_fracture_classifier.pt"

    config_payload = {
        "model_name": "FractureClassifierCNN",
        "task": "fracture",
        "parameter_count": param_count,
        "input_resolution": [224, 224],
        "input_channels": 1,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "class_imbalance": {
            "train_negatives": n_neg,
            "train_positives": n_pos,
            "pos_weight": pos_weight_value,
        },
        "augmentation": {
            "horizontal_flip_p": 0.5,
            "affine_degrees": [-8, 8],
            "affine_translate": [0.04, 0.04],
            "affine_scale": [0.96, 1.04],
        },
        "hyperparameters": {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "weight_decay": weight_decay,
            "optimizer": "AdamW",
            "scheduler": "ReduceLROnPlateau",
            "loss": "BCEWithLogitsLoss(weighted)",
            "primary_metric": "f1",
            "patience": patience,
            "seed": seed,
        },
    }

    config_file = OUTPUT_DIR / "training_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_payload, f, indent=2)

    engine = TrainingEngine(
        model=model,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        scheduler=scheduler,
    )

    logger.info("Starting training of FractureClassifierCNN for %d epochs...", epochs)
    fit_summary = engine.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=epochs,
        checkpoint_path=checkpoint_path,
        task_type="binary",
        primary_metric="f1",
        patience=patience,
        extra_meta=config_payload,
    )

    training_duration_sec = round(time.time() - start_time, 2)
    fit_summary["training_duration_seconds"] = training_duration_sec
    fit_summary["device"] = device_str

    history_file = OUTPUT_DIR / "history.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(fit_summary, f, indent=2)

    logger.info("Training completed in %.1f seconds", training_duration_sec)
    logger.info("History saved to %s", history_file)
    logger.info("Best checkpoint saved at %s", checkpoint_path)

    return fit_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Model C: Fracture Classifier CNN")
    parser.add_argument("--epochs", type=int, default=8, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    args = parser.parse_args()

    train_fracture_classifier(epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr, device_str=args.device)
