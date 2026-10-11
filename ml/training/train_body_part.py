"""Training script for Model B: Body-Part Classifier.

Trains BodyPartClassifierCNN on 4 anatomical classes: hand, leg, hip, shoulder.
Applies class weights in CrossEntropyLoss to address class imbalance.
Saves best model on validation macro_f1 to ml/saved_models/stage3/body_part/best_body_part.pt.
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
from ml.datasets.body_part_dataset import BodyPartDataset, create_body_part_dataloader, BODY_PART_CLASSES
from ml.models.body_part_classifier import BodyPartClassifierCNN
from ml.preprocessing.pipeline import XRayPreprocessor
from ml.training.engine import TrainingEngine

# Safety for truncated raw images
ImageFile.LOAD_TRUNCATED_IMAGES = True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_body_part")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPLITS_DIR = PROJECT_ROOT / "ml" / "datasets" / "splits" / "body_part"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "saved_models" / "stage3" / "body_part"


def load_normalized_samples(json_path: Path) -> List[NormalizedSample]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [NormalizedSample(**item) for item in data]


def train_body_part(
    epochs: int = 6,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-4,
    device_str: str = "cpu",
) -> Dict[str, Any]:
    """Train Model B (Body-Part Classifier)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device(device_str)

    preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)

    train_manifest = SPLITS_DIR / "train.json"
    val_manifest = SPLITS_DIR / "validation.json"
    summary_path = SPLITS_DIR / "summary.json"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_meta = json.load(f)
    raw_weights = summary_meta["train_class_weights"]

    # Class order: ["hand", "leg", "hip", "shoulder"]
    weights_tensor = torch.tensor(
        [raw_weights[name] for name in BODY_PART_CLASSES],
        dtype=torch.float32,
    ).to(device)

    logger.info("Using class weights: %s", {c: round(w.item(), 4) for c, w in zip(BODY_PART_CLASSES, weights_tensor)})

    logger.info("Loading training manifest: %s", train_manifest)
    train_samples = load_normalized_samples(train_manifest)
    logger.info("Loading validation manifest: %s", val_manifest)
    val_samples = load_normalized_samples(val_manifest)

    train_dataset = BodyPartDataset(train_samples, preprocessor=preprocessor)
    val_dataset = BodyPartDataset(val_samples, preprocessor=preprocessor)

    train_loader = create_body_part_dataloader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = create_body_part_dataloader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    logger.info("Train dataset size: %d | Val dataset size: %d", len(train_dataset), len(val_dataset))

    torch.manual_seed(42)
    model = BodyPartClassifierCNN(num_classes=len(BODY_PART_CLASSES)).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights_tensor)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    checkpoint_path = OUTPUT_DIR / "best_body_part.pt"

    engine = TrainingEngine(
        model=model,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
    )

    logger.info("Starting training of BodyPartClassifierCNN for %d epochs...", epochs)
    fit_summary = engine.fit(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=epochs,
        checkpoint_path=checkpoint_path,
        task_type="multiclass",
        primary_metric="macro_f1",
        class_names=BODY_PART_CLASSES,
        patience=3,
        extra_meta={
            "model_name": "BodyPartClassifierCNN",
            "classes": BODY_PART_CLASSES,
            "input_resolution": [224, 224],
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
            "class_weights": {c: float(w) for c, w in raw_weights.items()},
            "hyperparameters": {
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "weight_decay": weight_decay,
                "optimizer": "AdamW",
                "loss": "WeightedCrossEntropyLoss",
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

    parser = argparse.ArgumentParser(description="Train Body-Part Classifier CNN")
    parser.add_argument("--epochs", type=int, default=6, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    args = parser.parse_args()

    train_body_part(epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr)
