"""Structured Pydantic schema for Stage 5 Visual Explanation Engine.

Defines the contract for patient-safe, educational, and structured
interpretation of Stage 3 and Stage 4 ML results.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    """High-level system status for the explanation engine."""
    VALID_XRAY_FRACTURE_SUSPECTED = "VALID_XRAY_FRACTURE_SUSPECTED"
    VALID_XRAY_NO_FRACTURE_SIGNAL = "VALID_XRAY_NO_FRACTURE_SIGNAL"
    VALID_XRAY_UNCERTAIN = "VALID_XRAY_UNCERTAIN"
    BODY_PART_UNKNOWN = "BODY_PART_UNKNOWN"
    NON_XRAY = "NON_XRAY"
    XRAY_VALIDATION_UNCERTAIN = "XRAY_VALIDATION_UNCERTAIN"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    ERROR = "ERROR"


class BodyPartId(str, Enum):
    """Canonical body-part identifiers."""
    HAND = "hand"
    LEG = "leg"
    HIP = "hip"
    SHOULDER = "shoulder"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class FindingState(str, Enum):
    """Normalized finding outcomes."""
    SUSPECTED = "suspected"
    NO_SIGNAL = "no_signal"
    UNCERTAIN = "uncertain"
    UNSUPPORTED = "unsupported"
    NOT_ANALYZED = "not_analyzed"


class BodyRegionInfo(BaseModel):
    """Information about the identified anatomical region."""
    id: BodyPartId
    label: str
    is_supported: bool = True
    confidence: Optional[float] = None


class FindingInfo(BaseModel):
    """Information regarding the evaluated pathological finding (fracture only)."""
    id: str = "fracture"
    label: str = "Bone Fracture"
    state: FindingState
    probability: Optional[float] = None
    confidence: Optional[float] = None


class VisualExplanation(BaseModel):
    """Curated educational anatomical illustration metadata."""
    illustration_id: str
    illustration_path: str
    illustration_url: str
    educational_only: bool = True
    exact_location: bool = False
    title: str
    alt_text: str
    label_notice: str = "Example illustration — Not patient's X-ray"


class AttentionExplanation(BaseModel):
    """Model attention visualization metadata (Grad-CAM)."""
    available: bool = False
    type: str = "gradcam"
    overlay_path: Optional[str] = None
    overlay_base64: Optional[str] = None
    is_exact_localization: bool = False
    clinical_localization: bool = False
    disclaimer: str = (
        "Grad-CAM highlights areas that influenced the model's prediction. "
        "It is NOT a confirmed injury site or clinical localization."
    )


class LocalizationInfo(BaseModel):
    """Boundary metadata for diagnostic bounding-box localization."""
    available: bool = False
    status: str = "experimental_unverified"
    exact_location: bool = False
    reason: str = (
        "Localization model is experimental and unverified for clinical usage. "
        "Patient-facing bounding boxes are strictly disabled."
    )


class ExplanationResult(BaseModel):
    """Full structured explanation payload returned by the Visual Explanation Engine."""
    analysis_status: AnalysisStatus
    body_part: BodyRegionInfo
    finding: FindingInfo
    summary: str
    what_this_test_checks: str
    what_the_result_means: str
    next_step_message: str
    limitations: List[str] = Field(default_factory=list)
    visual: VisualExplanation
    attention: AttentionExplanation
    localization: LocalizationInfo = Field(default_factory=LocalizationInfo)
    medical_glossary: Dict[str, str] = Field(default_factory=dict)
    model_versions: Dict[str, str] = Field(default_factory=dict)
    language: str = "en"
    translation_keys: Dict[str, str] = Field(default_factory=dict)
