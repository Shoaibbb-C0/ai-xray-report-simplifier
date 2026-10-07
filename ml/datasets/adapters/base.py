"""Base schemas and abstractions for normalized X-ray dataset records."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedSample:
    """Normalized internal representation for an X-ray radiograph sample.
    
    Fields missing in original dataset sources remain None/empty rather than fabricated.
    """

    sample_id: str
    dataset: str
    image_path: str
    patient_id: Optional[str] = None
    study_id: Optional[str] = None
    body_part: Optional[str] = None  # e.g., 'hand', 'leg', 'hip', 'shoulder', 'chest', etc.
    view: Optional[str] = None       # e.g., 'AP', 'PA', 'LATERAL'
    is_abnormal: Optional[bool] = None  # True = abnormal/fracture, False = normal
    finding_labels: List[str] = field(default_factory=list)
    has_bbox: bool = False
    has_mask: bool = False
    split: Optional[str] = None  # 'train', 'validation', 'test'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert normalized sample to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedSample":
        """Instantiate a normalized sample from a dictionary."""
        return cls(**data)


class BaseDatasetAdapter(ABC):
    """Abstract base class for dataset adapters."""

    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir = Path(raw_dir)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique dataset identifier."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if raw dataset files are present in the expected directory."""
        pass

    @abstractmethod
    def load_manifest(self) -> List[NormalizedSample]:
        """Parse raw metadata and return normalized samples."""
        pass
