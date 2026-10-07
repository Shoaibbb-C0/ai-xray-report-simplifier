"""Central configuration and data definitions for AI X-Ray ML workflows.

This file establishes the foundational contract for future machine learning models,
preprocessing pipelines, and inference services. All models used in this project
are planned to be trained in-house using PyTorch on public medical research datasets.

NOTE: Safe placeholders and structure definitions are established here.
Final anatomical classes and abnormality taxonomies will be finalized during
the active dataset curation and training stages.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ImageRequirements:
    """Standard image pre-processing specifications for neural network input."""

    target_size: tuple[int, int] = (224, 224)
    channels: int = 1  # Grayscale X-ray input
    mean: float = 0.5  # Standard grayscale normalization mean
    std: float = 0.5   # Standard grayscale normalization std
    supported_formats: tuple[str, ...] = ("png", "jpg", "jpeg", "dicom")


# Body regions targeted for future validation and model routing
SUPPORTED_BODY_PARTS: List[str] = [
    "chest",
    "musculoskeletal",
    # TODO (Stage 2/3): Expand to specific anatomical subregions (e.g., wrist, knee, spine)
]

# Supported model architecture families for in-house training
SUPPORTED_MODEL_TYPES: List[str] = [
    "body_part_classifier",      # Classifies image anatomical view
    "pathology_detector",        # Multi-label or binary detection for findings
]

# Semantic model versioning registry (empty/placeholders until training stage)
MODEL_VERSIONS: Dict[str, str] = {
    "body_part_classifier": "v0.1.0-uninitialized",
    "chest_pathology_detector": "v0.1.0-uninitialized",
}

# Supported abnormality labels per anatomical region (to be populated from curated datasets)
SUPPORTED_ABNORMALITIES: Dict[str, List[str]] = {
    "chest": [
        # TODO (Stage 3): Populate based on public dataset labeling (e.g. CheXpert/NIH ChestX-ray14)
    ],
    "musculoskeletal": [
        # TODO (Stage 3): Populate based on public dataset labeling (e.g. MURA)
    ],
}

# Conservative decision thresholds to prevent misleading results in educational screening
CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    # Minimum probability threshold required to flag a possible finding
    "finding_detection_min_confidence": 0.65,
    # Threshold below which predictions are considered inconclusive
    "inconclusive_confidence_upper": 0.40,
}

IMAGE_SPEC = ImageRequirements()
