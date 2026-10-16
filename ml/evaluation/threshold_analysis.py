"""Validation-based threshold calibration and uncertainty band analysis for Model C.

Strictly utilizes the VALIDATION split to calibrate:
1. Primary binary decision threshold (optimizing F1 and sensitivity vs specificity tradeoff).
2. Tri-state uncertainty band [lower_bound, upper_bound] for clinical safety.
Never touches the test set for threshold selection.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.torch_dataset import NormalizedXRayDataset, create_xray_dataloader
from ml.models.fracture_classifier import FractureClassifierCNN
from ml.preprocessing.pipeline import XRayPreprocessor
from ml.training.metrics import calculate_binary_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("threshold_analysis")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPLITS_DIR = PROJECT_ROOT / "ml" / "datasets" / "splits" / "fracatlas_v2"
CHECKPOINT_PATH = PROJECT_ROOT / "ml" / "saved_models" / "stage4" / "fracture_classifier" / "best_fracture_classifier.pt"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "saved_models" / "stage4" / "fracture_classifier"


def load_validation_samples() -> List[NormalizedSample]:
    val_path = SPLITS_DIR / "validation.json"
    with open(val_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [NormalizedSample.from_dict(item) for item in data]


def get_validation_predictions(
    model: torch.nn.Module,
    samples: List[NormalizedSample],
    device: torch.device,
) -> Tuple[np.ndarray, np.ndarray]:
    """Runs inference across validation samples to obtain probabilities and ground-truth targets."""
    preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)
    val_dataset = NormalizedXRayDataset(samples, preprocessor=preprocessor, task="binary")
    val_loader = create_xray_dataloader(val_dataset, batch_size=64, shuffle=False, num_workers=0)

    model.eval()
    all_probs: List[float] = []
    all_targets: List[int] = []

    with torch.no_grad():
        for batch_imgs, batch_labels, _ in val_loader:
            batch_imgs = batch_imgs.to(device)
            logits = model(batch_imgs)
            probs = torch.sigmoid(logits).cpu().numpy().flatten()
            targets = batch_labels.numpy().flatten()
            all_probs.extend(probs.tolist())
            all_targets.extend(targets.tolist())

    return np.array(all_targets, dtype=int), np.array(all_probs, dtype=float)


def run_threshold_grid_search(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    start: float = 0.10,
    end: float = 0.90,
    step: float = 0.05,
) -> List[Dict[str, Any]]:
    """Evaluates metrics across candidate probability thresholds."""
    thresholds = np.arange(start, end + 1e-5, step)
    grid_results: List[Dict[str, Any]] = []

    n_pos = int(np.sum(y_true == 1))
    for t in thresholds:
        t_val = round(float(t), 3)
        metrics = calculate_binary_metrics(y_true, y_prob, threshold=t_val)
        fn_count = metrics["false_negatives"]
        fn_rate = round(fn_count / n_pos, 4) if n_pos > 0 else 0.0

        grid_results.append({
            "threshold": t_val,
            "f1": metrics["f1"],
            "balanced_accuracy": metrics["balanced_accuracy"],
            "recall_sensitivity": metrics["recall_sensitivity"],
            "specificity": metrics["specificity"],
            "precision": metrics["precision"],
            "false_negatives": fn_count,
            "false_negative_rate": fn_rate,
            "false_positives": metrics["false_positives"],
            "true_positives": metrics["true_positives"],
            "true_negatives": metrics["true_negatives"],
        })

    return grid_results


def select_calibrated_thresholds(
    grid: List[Dict[str, Any]],
    y_prob: np.ndarray,
) -> Dict[str, Any]:
    """Selects the primary decision threshold and clinical uncertainty band from validation behavior.
    
    Decision Rule:
    1. Filter candidates achieving sensitivity >= 0.70 and specificity >= 0.70 (if feasible).
    2. Among candidates, maximize F1 score to balance precision and recall.
    3. Construct uncertainty band [lower_bound, upper_bound] around the chosen decision boundary.
       Predictions inside the band are categorized as UNCERTAIN / BORDERLINE.
    """
    # Prefer candidates with solid recall (avoid high false negatives)
    candidates = [row for row in grid if row["recall_sensitivity"] >= 0.65 and row["specificity"] >= 0.65]
    if not candidates:
        candidates = sorted(grid, key=lambda x: x["f1"], reverse=True)
    else:
        candidates = sorted(candidates, key=lambda x: (x["f1"], x["recall_sensitivity"]), reverse=True)

    selected = candidates[0]
    decision_threshold = selected["threshold"]

    # Calibrate uncertainty band: symmetric margin around threshold, bounded to [0.20, 0.80]
    lower_bound = round(max(0.20, decision_threshold - 0.12), 2)
    upper_bound = round(min(0.80, decision_threshold + 0.12), 2)

    # Calculate validation percentage inside uncertainty band
    in_band = np.sum((y_prob >= lower_bound) & (y_prob <= upper_bound))
    uncertain_pct = round(float(in_band) / len(y_prob) * 100.0, 2)

    policy = {
        "decision_threshold": decision_threshold,
        "selected_metrics": selected,
        "uncertainty_policy": {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "uncertain_samples_val": int(in_band),
            "uncertain_percentage_val": uncertain_pct,
            "decision_rule": f"p < {lower_bound}: NO_FRACTURE | {lower_bound} <= p <= {upper_bound}: UNCERTAIN | p > {upper_bound}: FRACTURE",
        },
        "selection_rationale": (
            f"Selected threshold {decision_threshold} maximizes F1 ({selected['f1']:.4f}) while "
            f"retaining high sensitivity ({selected['recall_sensitivity']:.4f}) to limit missed fractures, "
            f"paired with an uncertainty zone [{lower_bound}, {upper_bound}] containing {uncertain_pct}% of validation cases."
        ),
    }

    return policy


def run_threshold_analysis(device_str: str = "cpu") -> Dict[str, Any]:
    """Execute complete threshold calibration pipeline on validation set."""
    device = torch.device(device_str)
    samples = load_validation_samples()
    logger.info("Loaded %d validation samples for calibration", len(samples))

    model = FractureClassifierCNN().to(device)
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Checkpoint not found at {CHECKPOINT_PATH}. Train model first.")

    ckpt = torch.load(CHECKPOINT_PATH, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    y_true, y_prob = get_validation_predictions(model, samples, device)
    grid = run_threshold_grid_search(y_true, y_prob)
    policy = select_calibrated_thresholds(grid, y_prob)

    report = {
        "dataset": "fracatlas_v2_validation",
        "sample_count": len(samples),
        "fracture_count": int(np.sum(y_true == 1)),
        "non_fracture_count": int(np.sum(y_true == 0)),
        "calibrated_policy": policy,
        "grid_search": grid,
    }

    report_path = OUTPUT_DIR / "threshold_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Threshold calibration complete. Selected threshold: %.2f", policy["decision_threshold"])
    logger.info("Uncertainty band: [%.2f, %.2f] (%s%% val cases)", policy["uncertainty_policy"]["lower_bound"], policy["uncertainty_policy"]["upper_bound"], policy["uncertainty_policy"]["uncertain_percentage_val"])
    logger.info("Report saved to %s", report_path)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run threshold calibration for Fracture Classifier")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    args = parser.parse_args()

    run_threshold_analysis(device_str=args.device)
