"""Reusable dataset and image validation utilities."""

from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

from ml.datasets.adapters.base import NormalizedSample


@dataclass
class ValidationReport:
    """Detailed summary of dataset health, file integrity, and distributions."""

    dataset_name: str
    total_samples: int = 0
    valid_images: int = 0
    invalid_images: int = 0
    missing_files: List[str] = field(default_factory=list)
    corrupted_files: List[str] = field(default_factory=list)
    duplicate_sample_ids: List[str] = field(default_factory=list)
    duplicate_image_paths: List[str] = field(default_factory=list)
    missing_metadata_count: int = 0
    class_distribution: Dict[str, int] = field(default_factory=dict)
    body_part_distribution: Dict[str, int] = field(default_factory=dict)
    image_modes: Dict[str, int] = field(default_factory=dict)
    min_dimensions: Optional[List[int]] = None
    max_dimensions: Optional[List[int]] = None
    errors: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """True if there are zero missing, corrupted, or duplicate files."""
        return (
            len(self.missing_files) == 0
            and len(self.corrupted_files) == 0
            and len(self.duplicate_sample_ids) == 0
            and len(self.duplicate_image_paths) == 0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return asdict(self)

    def summary_text(self) -> str:
        """Human-readable text summary of validation results."""
        lines = [
            f"=== Dataset Validation Report: {self.dataset_name} ===",
            f"Total Samples: {self.total_samples}",
            f"Valid Images: {self.valid_images}",
            f"Invalid/Corrupted Images: {self.invalid_images}",
            f"Missing Files: {len(self.missing_files)}",
            f"Duplicate Sample IDs: {len(self.duplicate_sample_ids)}",
            f"Duplicate Image Paths: {len(self.duplicate_image_paths)}",
            f"Class Distribution: {dict(self.class_distribution)}",
            f"Body-Part Distribution: {dict(self.body_part_distribution)}",
            f"Image Modes: {dict(self.image_modes)}",
        ]
        if self.min_dimensions and self.max_dimensions:
            lines.append(f"Dimensions: min={self.min_dimensions}, max={self.max_dimensions}")
        if self.errors:
            lines.append(f"Errors Logged: {len(self.errors)}")
            for err in self.errors[:5]:
                lines.append(f"  - {err}")
        return "\n".join(lines)


def validate_dataset(
    dataset_name: str,
    samples: List[NormalizedSample],
    verify_image_files: bool = True,
    sample_limit: Optional[int] = None,
) -> ValidationReport:
    """Validate a list of normalized samples for consistency, file existence, and image integrity."""
    report = ValidationReport(dataset_name=dataset_name, total_samples=len(samples))

    seen_sample_ids = set()
    seen_image_paths = set()
    class_counts = Counter()
    body_part_counts = Counter()
    mode_counts = Counter()

    widths = []
    heights = []

    to_check = samples[:sample_limit] if sample_limit else samples

    for s in to_check:
        # Check duplicate sample IDs
        if s.sample_id in seen_sample_ids:
            report.duplicate_sample_ids.append(s.sample_id)
        seen_sample_ids.add(s.sample_id)

        # Check duplicate image paths
        normalized_path = str(Path(s.image_path).resolve()) if s.image_path else ""
        if normalized_path in seen_image_paths:
            report.duplicate_image_paths.append(s.image_path)
        if normalized_path:
            seen_image_paths.add(normalized_path)

        # Class distribution
        if s.is_abnormal is True:
            class_counts["abnormal"] += 1
        elif s.is_abnormal is False:
            class_counts["normal"] += 1
        else:
            class_counts["unlabeled"] += 1

        # Body part distribution
        body_part_counts[s.body_part or "unknown"] += 1

        # Missing required metadata
        if not s.sample_id or not s.image_path:
            report.missing_metadata_count += 1

        # Verify image file on disk
        if verify_image_files:
            img_p = Path(s.image_path)
            if not img_p.exists():
                report.missing_files.append(str(s.image_path))
                report.invalid_images += 1
                report.errors.append(f"Missing file: {s.image_path}")
                continue

            try:
                with Image.open(img_p) as img:
                    img.verify()
                # Reopen to check dimensions and mode after verify()
                with Image.open(img_p) as img:
                    mode_counts[img.mode] += 1
                    widths.append(img.width)
                    heights.append(img.height)
                report.valid_images += 1
            except Exception as e:
                report.corrupted_files.append(str(s.image_path))
                report.invalid_images += 1
                report.errors.append(f"Corrupted image {s.image_path}: {e}")

    report.class_distribution = dict(class_counts)
    report.body_part_distribution = dict(body_part_counts)
    report.image_modes = dict(mode_counts)

    if widths and heights:
        report.min_dimensions = [min(widths), min(heights)]
        report.max_dimensions = [max(widths), max(heights)]

    return report
