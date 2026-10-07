"""Adapter for the FracAtlas musculoskeletal bone fracture dataset."""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from ml.datasets.adapters.base import BaseDatasetAdapter, NormalizedSample
from ml.datasets.validation import ValidationReport, validate_dataset


class FracAtlasAdapter(BaseDatasetAdapter):
    """Adapter for the FracAtlas dataset (Scientific Data / Figshare).
    
    Structure convention:
    raw/fracatlas/ (or raw/fracatlas/FracAtlas/)
      dataset.csv
      images/
        Fractured/
        Non_fractured/
      Annotations/
        COCO JSON/COCO_fracture_masks.json
        PASCAL VOC/*.xml
        YOLO/*.txt
    """

    SUPPORTED_REGIONS = ["hand", "leg", "hip", "shoulder", "mixed"]

    @property
    def name(self) -> str:
        return "fracatlas"

    def _locate_base(self) -> Optional[Path]:
        """Find the root directory containing dataset.csv."""
        if (self.raw_dir / "FracAtlas" / "dataset.csv").exists():
            return self.raw_dir / "FracAtlas"
        if (self.raw_dir / "dataset.csv").exists():
            return self.raw_dir
        return None

    def is_available(self) -> bool:
        """Checks if dataset.csv and image folders are present."""
        base = self._locate_base()
        if not base:
            return False
        return (base / "images" / "Fractured").exists() and (base / "images" / "Non_fractured").exists()

    def _get_coco_image_ids(self, base_dir: Path) -> Set[str]:
        """Load set of image filenames present in COCO segmentation masks."""
        coco_path = base_dir / "Annotations" / "COCO JSON" / "COCO_fracture_masks.json"
        if not coco_path.exists():
            return set()
        try:
            with open(coco_path, mode="r", encoding="utf-8") as f:
                data = json.load(f)
                return {img.get("file_name", "") for img in data.get("images", []) if img.get("file_name")}
        except Exception:
            return set()

    def load_manifest(self) -> List[NormalizedSample]:
        """Parse dataset.csv and return list of NormalizedSample objects."""
        if not self.is_available():
            return []

        base_dir = self._locate_base()
        if not base_dir:
            return []

        csv_path = base_dir / "dataset.csv"
        coco_mask_files = self._get_coco_image_ids(base_dir)
        pascal_dir = base_dir / "Annotations" / "PASCAL VOC"

        samples: List[NormalizedSample] = []

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                img_name = row.get("image_id", "").strip()
                if not img_name:
                    continue

                # Locate image in Fractured or Non_fractured
                img_path = base_dir / "images" / "Fractured" / img_name
                if not img_path.exists():
                    img_path = base_dir / "images" / "Non_fractured" / img_name

                # Determine body part from one-hot flags
                active_regions = [r for r in self.SUPPORTED_REGIONS if row.get(r, "0") == "1"]
                body_part = active_regions[0] if len(active_regions) == 1 else ("mixed" if len(active_regions) > 1 else "unknown")

                # Fracture flag
                is_fractured = row.get("fractured", "0") == "1"
                try:
                    fracture_count = int(row.get("fracture_count", "0"))
                except ValueError:
                    fracture_count = 1 if is_fractured else 0

                # View position
                views = []
                for v in ["frontal", "lateral", "oblique"]:
                    if row.get(v, "0") == "1":
                        views.append(v)
                view_str = "+".join(views) if views else None

                # Bounding box & mask annotations
                has_xml = (pascal_dir / f"{Path(img_name).stem}.xml").exists()
                has_bbox = is_fractured and (has_xml or fracture_count > 0)
                has_mask = img_name in coco_mask_files

                # Hardware and multiscan flags
                has_hardware = row.get("hardware", "0") == "1"
                is_multiscan = row.get("multiscan", "0") == "1"

                samples.append(
                    NormalizedSample(
                        sample_id=f"fracatlas_{Path(img_name).stem}",
                        dataset="fracatlas",
                        image_path=str(img_path),
                        body_part=body_part,
                        view=view_str,
                        is_abnormal=is_fractured,
                        finding_labels=["bone_fracture"] if is_fractured else [],
                        has_bbox=has_bbox,
                        has_mask=has_mask,
                        metadata={
                            "fracture_count": fracture_count,
                            "hardware": has_hardware,
                            "multiscan": is_multiscan,
                            "active_regions": active_regions,
                        },
                    )
                )

        return samples

    def validate_dataset(self, verify_images: bool = True, sample_limit: Optional[int] = None) -> ValidationReport:
        """Run comprehensive validation on FracAtlas samples and files."""
        samples = self.load_manifest()
        return validate_dataset("fracatlas", samples, verify_image_files=verify_images, sample_limit=sample_limit)
