"""Stage 5 Visual Explanation Engine package."""

from ml.explanation.schema import (
    AnalysisStatus,
    AttentionExplanation,
    BodyPartId,
    BodyRegionInfo,
    ExplanationResult,
    FindingInfo,
    FindingState,
    LocalizationInfo,
    VisualExplanation,
)
from ml.explanation.engine import VisualExplanationEngine
from ml.explanation.visual_mapper import resolve_illustration
from ml.explanation.glossary import get_glossary
from ml.explanation.translations import t

__all__ = [
    "AnalysisStatus",
    "AttentionExplanation",
    "BodyPartId",
    "BodyRegionInfo",
    "ExplanationResult",
    "FindingInfo",
    "FindingState",
    "LocalizationInfo",
    "VisualExplanation",
    "VisualExplanationEngine",
    "resolve_illustration",
    "get_glossary",
    "t",
]
