"""Model definitions for AI X-Ray Project."""

from ml.models.xray_validator import XRayValidatorCNN
from ml.models.body_part_classifier import BodyPartClassifierCNN

__all__ = ["XRayValidatorCNN", "BodyPartClassifierCNN"]
