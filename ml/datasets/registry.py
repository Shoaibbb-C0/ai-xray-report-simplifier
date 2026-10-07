"""Central dataset registry and availability tracker."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ml.datasets.adapters.base import BaseDatasetAdapter
from ml.datasets.adapters.fracatlas import FracAtlasAdapter
from ml.datasets.adapters.mura import MURAAdapter
from ml.datasets.adapters.chestxray14 import ChestXray14Adapter
from ml.datasets.adapters.vindr_spine import VinDrSpineAdapter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATASETS_DIR = PROJECT_ROOT / "ml" / "datasets" / "raw"


@dataclass
class DatasetMetadata:
    """Metadata specification for supported radiograph datasets."""

    dataset_id: str
    name: str
    purpose: str
    supported_anatomy: List[str]
    task_types: List[str]
    raw_dir: Path
    adapter_class: Type[BaseDatasetAdapter]
    license_name: str
    canonical_source: str
    citation: str
    is_restricted_access: bool = False

    def get_adapter(self) -> BaseDatasetAdapter:
        """Instantiate the adapter for this dataset."""
        return self.adapter_class(self.raw_dir)

    @property
    def availability_state(self) -> str:
        """Dynamic availability check reflecting filesystem state."""
        adapter = self.get_adapter()
        if adapter.is_available():
            return "available"
        if self.is_restricted_access:
            return "restricted"
        return "not_downloaded"


DATASET_REGISTRY: Dict[str, DatasetMetadata] = {
    "fracatlas": DatasetMetadata(
        dataset_id="fracatlas",
        name="FracAtlas",
        purpose="Fracture classification, localization, and segmentation on musculoskeletal radiographs.",
        supported_anatomy=["hand", "leg", "hip", "shoulder"],
        task_types=["classification", "localization", "segmentation"],
        raw_dir=RAW_DATASETS_DIR / "fracatlas",
        adapter_class=FracAtlasAdapter,
        license_name="Creative Commons Attribution 4.0 International (CC BY 4.0)",
        canonical_source="https://doi.org/10.6084/m9.figshare.22363012.v7",
        citation="Abedeen, I. et al. FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs. Sci Data 10, 521 (2023).",
        is_restricted_access=False,
    ),
    "mura": DatasetMetadata(
        dataset_id="mura",
        name="MURA (Musculoskeletal Radiographs)",
        purpose="Musculoskeletal abnormality detection and upper-extremity anatomical classification.",
        supported_anatomy=["elbow", "finger", "forearm", "hand", "humerus", "shoulder", "wrist"],
        task_types=["classification", "abnormality_detection"],
        raw_dir=RAW_DATASETS_DIR / "mura",
        adapter_class=MURAAdapter,
        license_name="Stanford Musculoskeletal Radiograph (MURA) Research Agreement",
        canonical_source="https://stanfordmlgroup.github.io/competitions/mura/",
        citation="Rajpurkar, P. et al. MURA: Large Dataset for Abnormality Detection in Musculoskeletal Radiographs. arXiv:1712.06957 (2017).",
        is_restricted_access=False,
    ),
    "chestxray14": DatasetMetadata(
        dataset_id="chestxray14",
        name="NIH ChestX-ray14",
        purpose="Thoracic pathology screening and multi-label findings classification from chest radiographs.",
        supported_anatomy=["chest"],
        task_types=["multi_label_classification"],
        raw_dir=RAW_DATASETS_DIR / "chestxray14",
        adapter_class=ChestXray14Adapter,
        license_name="NIH Clinical Center Open Commons License",
        canonical_source="https://nihcc.app.box.com/v/ChestXray-NIHCC",
        citation="Wang, X. et al. ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks. CVPR 2017.",
        is_restricted_access=False,
    ),
    "vindr_spine": DatasetMetadata(
        dataset_id="vindr_spine",
        name="VinDr-SpineXR",
        purpose="Comprehensive spine lesion detection, localization, and classification.",
        supported_anatomy=["spine"],
        task_types=["classification", "localization"],
        raw_dir=RAW_DATASETS_DIR / "vindr_spine",
        adapter_class=VinDrSpineAdapter,
        license_name="PhysioNet Credentialed Health Data License 1.5.0",
        canonical_source="https://physionet.org/content/vindr-spinexr/1.0.0/",
        citation="Nguyen, H.T. et al. VinDr-SpineXR: A large annotated medical image dataset for spine radiograph classification. PhysioNet (2021).",
        is_restricted_access=True,
    ),
}


def get_dataset_metadata(dataset_id: str) -> Optional[DatasetMetadata]:
    """Retrieve metadata for a registered dataset."""
    return DATASET_REGISTRY.get(dataset_id.lower())


def list_datasets() -> List[Dict[str, Any]]:
    """List all registered datasets with current availability."""
    return [
        {
            "dataset_id": meta.dataset_id,
            "name": meta.name,
            "availability": meta.availability_state,
            "supported_anatomy": meta.supported_anatomy,
            "license": meta.license_name,
            "restricted": meta.is_restricted_access,
        }
        for meta in DATASET_REGISTRY.values()
    ]
