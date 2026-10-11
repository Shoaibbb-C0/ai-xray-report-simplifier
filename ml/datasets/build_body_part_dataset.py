"""Generates balanced 4-class manifests and ambiguous holdout set for Model B (Body-Part Classifier)."""

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.splitting import check_data_leakage

TARGET_CLASSES = ["hand", "leg", "hip", "shoulder"]


def build_body_part_manifests() -> Dict[str, Any]:
    """Extract single-region anatomical samples and isolate composite mixed scans."""
    v2_dir = PROJECT_ROOT / "ml" / "datasets" / "splits" / "fracatlas_v2"
    bp_out_dir = PROJECT_ROOT / "ml" / "datasets" / "splits" / "body_part"
    bp_out_dir.mkdir(parents=True, exist_ok=True)

    splits_data = {
        "train": json.load(open(v2_dir / "train.json")),
        "validation": json.load(open(v2_dir / "validation.json")),
        "test": json.load(open(v2_dir / "test.json")),
    }

    filtered_splits: Dict[str, List[NormalizedSample]] = {"train": [], "validation": [], "test": []}
    ambiguous_mixed: List[NormalizedSample] = []

    for split_name, raw_list in splits_data.items():
        for item in raw_list:
            bp = (item.get("body_part") or "unknown").lower()
            sample = NormalizedSample.from_dict(item)
            if bp in TARGET_CLASSES:
                sample.split = split_name
                filtered_splits[split_name].append(sample)
            else:
                sample.split = "ambiguous_eval"
                ambiguous_mixed.append(sample)

    # Check leakage on target 4-class splits
    check_data_leakage(filtered_splits)

    # Export manifests
    manifest_paths = {}
    for split_name, sample_list in filtered_splits.items():
        out_p = bp_out_dir / f"{split_name}.json"
        with open(out_p, mode="w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in sample_list], f, indent=2)
        manifest_paths[split_name] = str(out_p)

    mixed_p = bp_out_dir / "ambiguous_mixed_test.json"
    with open(mixed_p, mode="w", encoding="utf-8") as f:
        json.dump([s.to_dict() for s in ambiguous_mixed], f, indent=2)
    manifest_paths["ambiguous_mixed"] = str(mixed_p)

    # Compute training class distribution & inverse weights
    train_counts = Counter(s.body_part for s in filtered_splits["train"])
    val_counts = Counter(s.body_part for s in filtered_splits["validation"])
    test_counts = Counter(s.body_part for s in filtered_splits["test"])

    n_train = len(filtered_splits["train"])
    n_classes = len(TARGET_CLASSES)
    # class_weight = N_total / (n_classes * count_c)
    class_weights = {
        c: round(n_train / (n_classes * train_counts[c]), 4)
        for c in TARGET_CLASSES
    }

    summary = {
        "dataset": "body_part_classifier",
        "target_classes": TARGET_CLASSES,
        "class_counts_train": dict(train_counts),
        "class_counts_val": dict(val_counts),
        "class_counts_test": dict(test_counts),
        "train_class_weights": class_weights,
        "ambiguous_mixed_count": len(ambiguous_mixed),
        "manifests": manifest_paths,
        "leakage_test_passed": True,
    }

    summary_p = bp_out_dir / "summary.json"
    with open(summary_p, mode="w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    res = build_body_part_manifests()
    print("Body-Part Classifier Manifests Generated:")
    print(json.dumps(res, indent=2))
