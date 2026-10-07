"""Adapter for Stanford MURA (Musculoskeletal Radiographs) dataset."""

import csv
from pathlib import Path
from typing import List, Optional

from ml.datasets.adapters.base import BaseDatasetAdapter, NormalizedSample


class MURAAdapter(BaseDatasetAdapter):
    """Adapter for parsing the Stanford MURA upper-extremity radiograph dataset.
    
    Expected study types:
    - ELBOW, FINGER, FOREARM, HAND, HUMERUS, SHOULDER, WRIST
    
    Folder structure convention:
    MURA-v1.1/
      train/XR_WRIST/patient00001/study1_positive/image1.png
      train_labeled_studies.csv
      valid_labeled_studies.csv
      train_image_paths.csv
      valid_image_paths.csv
    """

    SUPPORTED_STUDY_TYPES = {
        "XR_ELBOW": "elbow",
        "XR_FINGER": "finger",
        "XR_FOREARM": "forearm",
        "XR_HAND": "hand",
        "XR_HUMERUS": "humerus",
        "XR_SHOULDER": "shoulder",
        "XR_WRIST": "wrist",
    }

    @property
    def name(self) -> str:
        return "mura"

    def is_available(self) -> bool:
        """Checks whether the raw MURA dataset has been placed into raw_dir."""
        if not self.raw_dir.exists():
            return False
        # Check either directly or under nested MURA-v1.1 folder
        candidates = [
            self.raw_dir / "train_labeled_studies.csv",
            self.raw_dir / "MURA-v1.1" / "train_labeled_studies.csv",
        ]
        return any(p.exists() for p in candidates)

    def _locate_base(self) -> Path:
        """Find the root path containing CSV manifests."""
        if (self.raw_dir / "MURA-v1.1").exists():
            return self.raw_dir / "MURA-v1.1"
        return self.raw_dir

    def load_manifest(self) -> List[NormalizedSample]:
        """Parse MURA study lists and images into normalized samples."""
        if not self.is_available():
            return []

        base_dir = self._locate_base()
        samples: List[NormalizedSample] = []

        split_files = [
            ("train", base_dir / "train_labeled_studies.csv", base_dir / "train_image_paths.csv"),
            ("validation", base_dir / "valid_labeled_studies.csv", base_dir / "valid_image_paths.csv"),
        ]

        for split_name, study_csv, image_csv in split_files:
            if not study_csv.exists():
                continue

            # Map study path -> label (1 = abnormal/positive, 0 = normal/negative)
            study_labels = {}
            with open(study_csv, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        study_path_key = row[0].strip().rstrip("/")
                        study_labels[study_path_key] = (int(row[1]) == 1)

            # If image paths file exists, map each individual radiograph
            if image_csv.exists():
                with open(image_csv, mode="r", encoding="utf-8") as f:
                    for line in f:
                        rel_img_path = line.strip()
                        if not rel_img_path:
                            continue
                        
                        full_img_path = (self.raw_dir / rel_img_path) if not (base_dir / rel_img_path).exists() else (base_dir / rel_img_path)
                        parts = Path(rel_img_path).parts
                        
                        # Expected parts: [..., split, 'XR_WRIST', 'patient00001', 'study1_positive', 'image1.png']
                        study_type_raw = None
                        patient_id = None
                        study_id = None
                        
                        for p in parts:
                            if p in self.SUPPORTED_STUDY_TYPES:
                                study_type_raw = p
                            elif p.startswith("patient"):
                                patient_id = p
                            elif p.startswith("study"):
                                study_id = p

                        body_part = self.SUPPORTED_STUDY_TYPES.get(study_type_raw, "unknown")
                        study_key = "/".join(parts[:-1]) if len(parts) > 1 else ""
                        is_abnormal = study_labels.get(study_key, None)
                        if is_abnormal is None and study_id:
                            is_abnormal = ("positive" in study_id.lower())

                        sample_id = f"mura_{patient_id or 'unknown'}_{study_id or 'unknown'}_{Path(rel_img_path).stem}"
                        samples.append(
                            NormalizedSample(
                                sample_id=sample_id,
                                dataset="mura",
                                image_path=str(full_img_path),
                                patient_id=patient_id,
                                study_id=f"{patient_id}_{study_id}" if patient_id and study_id else study_id,
                                body_part=body_part,
                                is_abnormal=is_abnormal,
                                finding_labels=["musculoskeletal_abnormality"] if is_abnormal else [],
                                split=split_name,
                                metadata={
                                    "original_study_type": study_type_raw,
                                    "original_relative_path": rel_img_path,
                                },
                            )
                        )

        return samples
