"""Adapter for VinDr-SpineXR dataset (Restricted Access via PhysioNet)."""

import csv
from pathlib import Path
from typing import List

from ml.datasets.adapters.base import BaseDatasetAdapter, NormalizedSample


class VinDrSpineAdapter(BaseDatasetAdapter):
    """Adapter for VinDr-SpineXR (Spine Radiographs).
    
    IMPORTANT:
    This dataset requires a formal credentialed account and signed Data Use Agreement (DUA)
    on PhysioNet (Goldberger et al.). It is restricted access by policy.
    This adapter provides the structural contract for future ingestion once credentials
    and data are manually arranged by the user.
    """

    @property
    def name(self) -> str:
        return "vindr_spine"

    def is_available(self) -> bool:
        """Indicates whether authenticated user has placed VinDr-SpineXR data in raw_dir."""
        if not self.raw_dir.exists():
            return False
        # Expected PhysioNet annotations directory
        return (self.raw_dir / "annotations" / "train.csv").exists() or (self.raw_dir / "train.csv").exists()

    def load_manifest(self) -> List[NormalizedSample]:
        """Parse annotations if present."""
        if not self.is_available():
            return []

        csv_path = self.raw_dir / "annotations" / "train.csv"
        if not csv_path.exists():
            csv_path = self.raw_dir / "train.csv"

        samples: List[NormalizedSample] = []
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                img_id = row.get("image_id", "").strip()
                if not img_id:
                    continue
                label_name = row.get("lesion_type", "").strip()
                img_path = self.raw_dir / "train" / f"{img_id}.dicom"
                if not img_path.exists():
                    img_path = self.raw_dir / "train" / f"{img_id}.png"

                samples.append(
                    NormalizedSample(
                        sample_id=f"vindr_spine_{img_id}",
                        dataset="vindr_spine",
                        image_path=str(img_path),
                        study_id=row.get("study_id", "").strip() or None,
                        body_part="spine",
                        is_abnormal=(label_name.lower() != "no finding" if label_name else None),
                        finding_labels=[label_name] if label_name and label_name.lower() != "no finding" else [],
                        has_bbox=("xmin" in row),
                        metadata={"lesion_type": label_name},
                    )
                )

        return samples
