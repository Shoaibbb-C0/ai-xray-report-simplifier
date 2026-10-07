"""Adapter for NIH ChestX-ray14 dataset."""

import csv
from pathlib import Path
from typing import List

from ml.datasets.adapters.base import BaseDatasetAdapter, NormalizedSample


class ChestXray14Adapter(BaseDatasetAdapter):
    """Adapter for NIH ChestX-ray14 dataset.
    
    Clinical Note:
    NIH ChestX-ray14 labels were automatically extracted from radiology reports
    via natural language processing (NLP) and text mining. As such, finding labels
    represent text-mined radiological mentions with known noise levels (~90% accuracy)
    and must be interpreted with clinical caution rather than considered gold-standard ground truth.
    Findings are multi-label.
    """

    KNOWN_LABELS = {
        "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
        "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
        "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
    }

    @property
    def name(self) -> str:
        return "chestxray14"

    def is_available(self) -> bool:
        """Checks whether the metadata CSV exists in raw_dir."""
        if not self.raw_dir.exists():
            return False
        candidates = [
            self.raw_dir / "Data_Entry_2017_v2020.csv",
            self.raw_dir / "Data_Entry_2017.csv",
        ]
        return any(p.exists() for p in candidates)

    def _locate_csv(self) -> Path:
        for fname in ["Data_Entry_2017_v2020.csv", "Data_Entry_2017.csv"]:
            p = self.raw_dir / fname
            if p.exists():
                return p
        raise FileNotFoundError(f"No metadata CSV found in {self.raw_dir}")

    def load_manifest(self) -> List[NormalizedSample]:
        """Parse NIH ChestX-ray14 metadata into normalized samples."""
        if not self.is_available():
            return []

        csv_path = self._locate_csv()
        samples: List[NormalizedSample] = []

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                img_name = row.get("Image Index", "").strip()
                if not img_name:
                    continue

                raw_findings = row.get("Finding Labels", "").strip()
                labels = [
                    lbl.strip()
                    for lbl in raw_findings.split("|")
                    if lbl.strip() and lbl.strip() != "No Finding"
                ]

                patient_id = row.get("Patient ID", "").strip() or None
                view = row.get("View Position", "").strip() or None
                is_abnormal = len(labels) > 0 if raw_findings else None

                # Search for image file under raw_dir or images subdirectory
                img_path = self.raw_dir / "images" / img_name
                if not img_path.exists():
                    img_path = self.raw_dir / img_name

                samples.append(
                    NormalizedSample(
                        sample_id=f"chestxray14_{Path(img_name).stem}",
                        dataset="chestxray14",
                        image_path=str(img_path),
                        patient_id=f"patient_{patient_id}" if patient_id else None,
                        body_part="chest",
                        view=view,
                        is_abnormal=is_abnormal,
                        finding_labels=labels,
                        metadata={
                            "patient_age": row.get("Patient Age"),
                            "patient_gender": row.get("Patient Gender"),
                            "follow_up_number": row.get("Follow-up #"),
                            "view_position": view,
                        },
                    )
                )

        return samples
