"""Reusable dataset parser and audit utility for FracAtlas fracture localization annotations."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FRACATLAS_DIR = PROJECT_ROOT / "ml" / "datasets" / "raw" / "fracatlas" / "FracAtlas"
PASCAL_DIR = RAW_FRACATLAS_DIR / "Annotations" / "PASCAL VOC"
IMAGES_DIR = RAW_FRACATLAS_DIR / "images"


@dataclass
class BoundingBox:
    """Bounding box in pixel coordinates."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    label: str = "fracture"

    @property
    def width(self) -> float:
        return max(0.0, self.xmax - self.xmin)

    @property
    def height(self) -> float:
        return max(0.0, self.ymax - self.ymin)

    @property
    def area(self) -> float:
        return self.width * self.height

    def is_valid(self) -> bool:
        return self.xmax > self.xmin and self.ymax > self.ymin

    def to_normalized(self, img_w: float, img_h: float) -> Tuple[float, float, float, float]:
        """Convert to [0.0, 1.0] relative coordinates."""
        if img_w <= 0 or img_h <= 0:
            return 0.0, 0.0, 0.0, 0.0
        return (
            max(0.0, min(1.0, self.xmin / img_w)),
            max(0.0, min(1.0, self.ymin / img_h)),
            max(0.0, min(1.0, self.xmax / img_w)),
            max(0.0, min(1.0, self.ymax / img_h)),
        )

    def to_letterbox_224(self, orig_w: float, orig_h: float, target_size: int = 224) -> Tuple[float, float, float, float]:
        """Map bounding box to 224x224 letterboxed coordinate space."""
        if orig_w <= 0 or orig_h <= 0:
            return 0.0, 0.0, 0.0, 0.0

        scale = min(target_size / orig_w, target_size / orig_h)
        scaled_w = orig_w * scale
        scaled_h = orig_h * scale
        pad_x = (target_size - scaled_w) / 2.0
        pad_y = (target_size - scaled_h) / 2.0

        lx1 = pad_x + self.xmin * scale
        ly1 = pad_y + self.ymin * scale
        lx2 = pad_x + self.xmax * scale
        ly2 = pad_y + self.ymax * scale

        return lx1, ly1, lx2, ly2


@dataclass
class LocalizationRecord:
    image_id: str
    image_path: str
    orig_width: int
    orig_height: int
    boxes: List[BoundingBox]

    @property
    def is_fractured(self) -> bool:
        return len(self.boxes) > 0

    @property
    def is_single_box(self) -> bool:
        return len(self.boxes) == 1

    @property
    def is_multi_box(self) -> bool:
        return len(self.boxes) > 1


def parse_pascal_voc_xml(xml_path: Path) -> Optional[LocalizationRecord]:
    """Parses a single Pascal VOC XML annotation file."""
    if not xml_path.exists():
        return None

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        filename = root.findtext("filename") or f"{xml_path.stem}.jpg"
        size_elem = root.find("size")
        width = int(size_elem.findtext("width", "0")) if size_elem is not None else 0
        height = int(size_elem.findtext("height", "0")) if size_elem is not None else 0

        # Locate image file
        img_path = IMAGES_DIR / "Fractured" / filename
        if not img_path.exists():
            img_path = IMAGES_DIR / "Non_fractured" / filename

        boxes: List[BoundingBox] = []
        for obj in root.findall("object"):
            label = obj.findtext("name", "fracture").strip()
            b = obj.find("bndbox")
            if b is not None:
                xmin = float(b.findtext("xmin", "0"))
                ymin = float(b.findtext("ymin", "0"))
                xmax = float(b.findtext("xmax", "0"))
                ymax = float(b.findtext("ymax", "0"))
                box = BoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, label=label)
                if box.is_valid():
                    boxes.append(box)

        return LocalizationRecord(
            image_id=xml_path.stem,
            image_path=str(img_path),
            orig_width=width,
            orig_height=height,
            boxes=boxes,
        )
    except Exception:
        return None


def run_localization_audit() -> Dict[str, Any]:
    """Performs a comprehensive audit across all FracAtlas localization annotations."""
    if not PASCAL_DIR.exists():
        return {"error": "PASCAL VOC directory not found"}

    xml_files = sorted(list(PASCAL_DIR.glob("*.xml")))
    total_files = len(xml_files)

    annotated_fracture_images = 0
    total_boxes = 0
    single_box_images = 0
    multi_box_images = 0
    zero_box_images = 0
    invalid_boxes = 0
    box_relative_areas: List[float] = []

    for xml_p in xml_files:
        rec = parse_pascal_voc_xml(xml_p)
        if rec is None:
            continue

        n_b = len(rec.boxes)
        if n_b == 0:
            zero_box_images += 1
        elif n_b == 1:
            annotated_fracture_images += 1
            single_box_images += 1
            total_boxes += 1
        else:
            annotated_fracture_images += 1
            multi_box_images += 1
            total_boxes += n_b

        for b in rec.boxes:
            if not b.is_valid():
                invalid_boxes += 1
            elif rec.orig_width > 0 and rec.orig_height > 0:
                rel_area = (b.width * b.height) / (rec.orig_width * rec.orig_height)
                box_relative_areas.append(rel_area)

    mean_area = float(sum(box_relative_areas) / len(box_relative_areas)) if box_relative_areas else 0.0

    return {
        "formats_present": ["PASCAL VOC XML", "YOLO TXT", "COCO JSON"],
        "total_xml_files": total_files,
        "annotated_fracture_images": annotated_fracture_images,
        "total_boxes": total_boxes,
        "single_box_images": single_box_images,
        "multi_box_images": multi_box_images,
        "zero_box_images": zero_box_images,
        "invalid_annotations": invalid_boxes,
        "box_size_distribution": {
            "min_relative_area": round(float(min(box_relative_areas)), 5) if box_relative_areas else 0.0,
            "max_relative_area": round(float(max(box_relative_areas)), 5) if box_relative_areas else 0.0,
            "mean_relative_area": round(mean_area, 5),
            "median_relative_area": round(float(sorted(box_relative_areas)[len(box_relative_areas) // 2]), 5) if box_relative_areas else 0.0,
        },
    }
