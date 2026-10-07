"""Exploratory Data Analysis (EDA) and summary reporting tool for datasets."""

import argparse
import json
from collections import Counter
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Any, Dict, List, Optional
from ml.datasets.registry import DATASET_REGISTRY, list_datasets
from ml.datasets.validation import validate_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "ml" / "datasets" / "splits"


def generate_dataset_report(dataset_id: str, limit_image_checks: Optional[int] = None) -> Dict[str, Any]:
    """Generate detailed EDA metrics for a given dataset."""
    meta = DATASET_REGISTRY.get(dataset_id.lower())
    if not meta:
        raise ValueError(f"Dataset '{dataset_id}' not found in registry.")

    adapter = meta.get_adapter()
    if not adapter.is_available():
        return {
            "dataset_id": dataset_id,
            "name": meta.name,
            "status": meta.availability_state,
            "available": False,
            "message": "Dataset not available on local filesystem.",
        }

    samples = adapter.load_manifest()
    validation_report = validate_dataset(
        dataset_name=dataset_id,
        samples=samples,
        verify_image_files=True,
        sample_limit=limit_image_checks,
    )

    # Compute patient/study counts where available
    unique_patients = len({s.patient_id for s in samples if s.patient_id})
    unique_studies = len({s.study_id for s in samples if s.study_id})

    report = {
        "dataset_id": dataset_id,
        "name": meta.name,
        "status": "available",
        "total_images": len(samples),
        "unique_patients": unique_patients if unique_patients > 0 else "N/A",
        "unique_studies": unique_studies if unique_studies > 0 else "N/A",
        "class_distribution": validation_report.class_distribution,
        "body_part_distribution": validation_report.body_part_distribution,
        "image_modes": validation_report.image_modes,
        "dimension_range": {
            "min": validation_report.min_dimensions,
            "max": validation_report.max_dimensions,
        },
        "clean_manifest": validation_report.is_clean,
    }

    return report


def run_full_eda(export_json: bool = True) -> Dict[str, Any]:
    """Execute EDA across all available datasets and print concise summary."""
    print("=" * 65)
    print("AI X-Ray Project — Dataset Exploration & Health Report")
    print("=" * 65)

    full_report: Dict[str, Any] = {"datasets": {}}

    for d_id, meta in DATASET_REGISTRY.items():
        state = meta.availability_state
        print(f"\n[Dataset: {meta.name} ({d_id})]")
        print(f"Status: {state.upper()} | Anatomy: {', '.join(meta.supported_anatomy)}")

        if state == "available":
            data = generate_dataset_report(d_id)
            full_report["datasets"][d_id] = data
            print(f"  • Total Images: {data['total_images']}")
            print(f"  • Patients: {data['unique_patients']} | Studies: {data['unique_studies']}")
            print(f"  • Classes: {data['class_distribution']}")
            print(f"  • Body Parts: {data['body_part_distribution']}")
            print(f"  • Image Modes: {data['image_modes']}")
            print(f"  • Image Dimensions (min/max): {data['dimension_range']['min']} to {data['dimension_range']['max']}")
            print(f"  • Clean Manifest: {'YES' if data['clean_manifest'] else 'ISSUES DETECTED'}")
        else:
            full_report["datasets"][d_id] = {
                "dataset_id": d_id,
                "status": state,
                "message": f"Dataset currently in '{state}' state.",
            }
            print(f"  • Note: {state.replace('_', ' ').capitalize()} - awaiting placement or access authorization.")

    print("\n" + "=" * 65)

    if export_json:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = OUTPUT_DIR / "eda_report.json"
        with open(report_path, mode="w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2)
        print(f"Machine-readable EDA report exported to: {report_path}")

    return full_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset EDA reporting tool.")
    parser.add_argument("--dataset", type=str, default=None, help="Specific dataset ID to evaluate")
    args = parser.parse_args()

    if args.dataset:
        report = generate_dataset_report(args.dataset)
        print(json.dumps(report, indent=2))
    else:
        run_full_eda()
