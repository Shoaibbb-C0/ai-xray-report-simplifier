"""Generates balanced, leak-free manifests for Model A (X-Ray Validator)."""

import json
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.splitting import check_data_leakage

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def build_validator_manifests() -> Dict[str, Any]:
    """Combine positive radiographs (FracAtlas v2) and negative multi-source imagery."""
    v2_dir = PROJECT_ROOT / "ml" / "datasets" / "splits" / "fracatlas_v2"
    val_out_dir = PROJECT_ROOT / "ml" / "datasets" / "splits" / "validator"
    val_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load positive FracAtlas splits
    pos_train = json.load(open(v2_dir / "train.json"))
    pos_val = json.load(open(v2_dir / "validation.json"))
    pos_test = json.load(open(v2_dir / "test.json"))

    # Convert positive samples to validator format (label 1 = X-ray)
    def to_validator_pos(s_dict: Dict[str, Any]) -> NormalizedSample:
        return NormalizedSample(
            sample_id=s_dict["sample_id"],
            dataset="fracatlas",
            image_path=s_dict["image_path"],
            patient_id=s_dict.get("patient_id"),
            body_part=s_dict.get("body_part"),
            is_abnormal=True,  # In validator context: True = X-Ray
            finding_labels=["xray"],
            split=s_dict.get("split"),
            metadata={"source_category": "radiograph", "original_split": s_dict.get("split")},
        )

    validator_pos_train = [to_validator_pos(s) for s in pos_train]
    validator_pos_val = [to_validator_pos(s) for s in pos_val]
    validator_pos_test = [to_validator_pos(s) for s in pos_test]

    # 2. Negative Source A: ImageNet natural images (1000 images)
    imgnet_dir = PROJECT_ROOT / "ml" / "datasets" / "raw" / "negative_samples" / "imagenet_samples"
    imgnet_files = sorted(list(imgnet_dir.glob("*.JPEG")) + list(imgnet_dir.glob("*.jpg")) + list(imgnet_dir.glob("*.png")))

    # Deterministic split: 700 train, 150 val, 150 test
    imgnet_train_files = imgnet_files[:700]
    imgnet_val_files = imgnet_files[700:850]
    imgnet_test_files = imgnet_files[850:1000]

    def to_validator_neg(p: Path, source_name: str, split_name: str) -> NormalizedSample:
        return NormalizedSample(
            sample_id=f"neg_{source_name}_{p.stem}",
            dataset=source_name,
            image_path=str(p.resolve()),
            is_abnormal=False,  # False = Non-X-Ray
            finding_labels=["non_xray"],
            split=split_name,
            metadata={"source_category": source_name},
        )

    neg_a_train = [to_validator_neg(p, "imagenet_natural", "train") for p in imgnet_train_files]
    neg_a_val = [to_validator_neg(p, "imagenet_natural", "validation") for p in imgnet_val_files]
    neg_a_test = [to_validator_neg(p, "imagenet_natural", "test") for p in imgnet_test_files]

    # 3. Negative Source B: RetinaMNIST 224x224 (1600 images)
    retina_dir = PROJECT_ROOT / "ml" / "datasets" / "raw" / "negative_samples" / "retinamnist"
    retina_train_files = sorted(list(retina_dir.glob("retina_train_*.png")))
    retina_val_files = sorted(list(retina_dir.glob("retina_val_*.png")))
    retina_test_files = sorted(list(retina_dir.glob("retina_test_*.png")))

    neg_b_train = [to_validator_neg(p, "retinamnist_ophthalmology", "train") for p in retina_train_files]
    neg_b_val = [to_validator_neg(p, "retinamnist_ophthalmology", "validation") for p in retina_val_files]
    neg_b_test = [to_validator_neg(p, "retinamnist_ophthalmology", "test") for p in retina_test_files]

    # Combine into composite splits
    train_set = validator_pos_train + neg_a_train + neg_b_train
    val_set = validator_pos_val + neg_a_val + neg_b_val
    test_set = validator_pos_test + neg_a_test + neg_b_test

    splits = {
        "train": train_set,
        "validation": val_set,
        "test": test_set,
    }

    # Verify leakage
    check_data_leakage(splits)

    # 4. Negative Source C (OOD Holdout): DermaMNIST
    derma_dir = PROJECT_ROOT / "ml" / "datasets" / "raw" / "negative_samples" / "dermamnist"
    derma_files = sorted(list(derma_dir.glob("derma_ood_*.png")))
    ood_set = [to_validator_neg(p, "dermamnist_dermatology_ood", "ood_test") for p in derma_files]

    # Export manifests
    manifest_paths = {}
    for k, v in splits.items():
        out_p = val_out_dir / f"{k}.json"
        with open(out_p, mode="w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in v], f, indent=2)
        manifest_paths[k] = str(out_p)

    ood_p = val_out_dir / "ood_test.json"
    with open(ood_p, mode="w", encoding="utf-8") as f:
        json.dump([s.to_dict() for s in ood_set], f, indent=2)
    manifest_paths["ood_test"] = str(ood_p)

    summary = {
        "dataset": "xray_validator",
        "train_count": len(train_set),
        "train_pos": len(validator_pos_train),
        "train_neg": len(neg_a_train) + len(neg_b_train),
        "val_count": len(val_set),
        "val_pos": len(validator_pos_val),
        "val_neg": len(neg_a_val) + len(neg_b_val),
        "test_count": len(test_set),
        "test_pos": len(validator_pos_test),
        "test_neg": len(neg_a_test) + len(neg_b_test),
        "test_neg_per_source": {
            "imagenet_natural": len(neg_a_test),
            "retinamnist_ophthalmology": len(neg_b_test),
        },
        "ood_count": len(ood_set),
        "ood_source": "dermamnist_dermatology",
        "manifests": manifest_paths,
    }

    summary_file = val_out_dir / "summary.json"
    with open(summary_file, mode="w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    res = build_validator_manifests()
    print("X-Ray Validator Manifests Generated:")
    print(json.dumps(res, indent=2))
