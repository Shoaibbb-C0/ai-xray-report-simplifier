"""Evaluation script for Model B (Body-Part Classifier).

Computes comprehensive metrics on:
1. Canonical Test Set (4 anatomical classes: hand, leg, hip, shoulder)
   - Macro F1, Balanced Accuracy, Overall Accuracy
   - Per-class Precision, Recall, F1, Support
   - Full Confusion Matrix
2. UNKNOWN Rejection Assessment:
   - Evaluates on FracAtlas ambiguous mixed-anatomy images
   - Tests confidence-based rejection policy (e.g. max softmax prob < 0.60 -> UNKNOWN)

Outputs JSON evaluation report.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import torch
from PIL import ImageFile

from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.body_part_dataset import BodyPartDataset, create_body_part_dataloader, BODY_PART_CLASSES
from ml.models.body_part_classifier import BodyPartClassifierCNN
from ml.preprocessing.pipeline import XRayPreprocessor
from ml.training.metrics import calculate_multiclass_metrics

ImageFile.LOAD_TRUNCATED_IMAGES = True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_body_part")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPLITS_DIR = PROJECT_ROOT / "ml" / "datasets" / "splits" / "body_part"
CHECKPOINT_PATH = PROJECT_ROOT / "ml" / "saved_models" / "stage3" / "body_part" / "best_body_part.pt"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "saved_models" / "stage3" / "body_part"


def load_normalized_samples(json_path: Path) -> List[NormalizedSample]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [NormalizedSample(**item) for item in data]


def run_evaluation() -> Dict[str, Any]:
    device = torch.device("cpu")
    preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)

    logger.info("Loading checkpoint from %s", CHECKPOINT_PATH)
    checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
    model = BodyPartClassifierCNN(num_classes=len(BODY_PART_CLASSES)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # 1. Evaluate Canonical Test Set
    test_samples = load_normalized_samples(SPLITS_DIR / "test.json")
    test_dataset = BodyPartDataset(test_samples, preprocessor=preprocessor)
    test_loader = create_body_part_dataloader(test_dataset, batch_size=64, shuffle=False, num_workers=0)

    all_targets: List[int] = []
    all_probs: List[np.ndarray] = []

    with torch.no_grad():
        for imgs, labels, _ in test_loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            targets = labels.cpu().numpy()
            all_probs.append(probs)
            all_targets.extend(targets.tolist())

    y_true = np.array(all_targets, dtype=np.int64)
    y_prob = np.vstack(all_probs)

    metrics = calculate_multiclass_metrics(y_true, y_prob, class_names=BODY_PART_CLASSES)

    # 2. Evaluate Rejection on Ambiguous Mixed Images
    mixed_manifest = SPLITS_DIR / "ambiguous_mixed_test.json"
    mixed_samples = load_normalized_samples(mixed_manifest)
    logger.info("Evaluating UNKNOWN rejection policy on %d mixed samples...", len(mixed_samples))

    mixed_probs: List[np.ndarray] = []
    with torch.no_grad():
        for s in mixed_samples:
            img_tensor = preprocessor(s.image_path).unsqueeze(0).to(device)
            logits = model(img_tensor)
            prob = torch.softmax(logits, dim=1).cpu().numpy()[0]
            mixed_probs.append(prob)

    mixed_probs_arr = np.array(mixed_probs)
    max_confidences = np.max(mixed_probs_arr, axis=1)

    # Rejection policy thresholds
    thresholds = [0.50, 0.60, 0.70, 0.80]
    rejection_rates = {f"rejection_rate_thresh_{t}": round(float(np.mean(max_confidences < t)), 4) for t in thresholds}

    # Selected operational rejection threshold = 0.60
    selected_threshold = 0.60
    unknown_count = int(np.sum(max_confidences < selected_threshold))

    report = {
        "model": "BodyPartClassifierCNN",
        "checkpoint": str(CHECKPOINT_PATH),
        "target_classes": BODY_PART_CLASSES,
        "test_metrics": metrics,
        "unknown_rejection_policy": {
            "selected_confidence_threshold": selected_threshold,
            "decision_rule": f"max_prob < {selected_threshold} -> UNKNOWN / REJECT",
            "ambiguous_mixed_samples_tested": len(mixed_samples),
            "rejected_as_unknown_count": unknown_count,
            "rejection_percentage": round(unknown_count / len(mixed_samples) * 100, 2),
            "threshold_analysis": rejection_rates,
            "median_confidence_mixed": round(float(np.median(max_confidences)), 4),
            "mean_confidence_mixed": round(float(np.mean(max_confidences)), 4),
        },
    }

    report_path = OUTPUT_DIR / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Body-Part evaluation report saved to %s", report_path)
    return report


if __name__ == "__main__":
    run_evaluation()
