"""PyTorch Dataset implementation for normalized radiograph manifests."""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import torch
from torch.utils.data import DataLoader, Dataset

from ml.datasets.adapters.base import NormalizedSample
from ml.preprocessing.pipeline import XRayPreprocessor


class NormalizedXRayDataset(Dataset):
    """PyTorch Dataset consuming normalized radiograph samples.
    
    Supports:
    - 'binary': Abnormal/normal (e.g. fracture vs intact) -> torch.float32 [1]
    - 'body_part': Anatomical category index -> torch.int64 []
    - 'multilabel': Multi-hot vector across findings -> torch.float32 [num_classes]
    """

    BODY_PART_CLASSES = ["hand", "leg", "hip", "shoulder", "mixed", "chest", "elbow", "finger", "forearm", "humerus", "wrist", "spine", "unknown"]

    def __init__(
        self,
        samples: List[NormalizedSample],
        preprocessor: Optional[XRayPreprocessor] = None,
        task: str = "binary",
        multilabel_classes: Optional[List[str]] = None,
    ) -> None:
        self.samples = samples
        self.preprocessor = preprocessor or XRayPreprocessor()
        self.task = task
        self.multilabel_classes = multilabel_classes or []

    def __len__(self) -> int:
        return len(self.samples)

    def _get_label(self, sample: NormalizedSample) -> torch.Tensor:
        if self.task == "binary":
            val = 1.0 if sample.is_abnormal else 0.0
            return torch.tensor([val], dtype=torch.float32)

        elif self.task == "body_part":
            bp = (sample.body_part or "unknown").lower()
            idx = self.BODY_PART_CLASSES.index(bp) if bp in self.BODY_PART_CLASSES else self.BODY_PART_CLASSES.index("unknown")
            return torch.tensor(idx, dtype=torch.int64)

        elif self.task == "multilabel":
            if not self.multilabel_classes:
                return torch.zeros(0, dtype=torch.float32)
            vec = torch.zeros(len(self.multilabel_classes), dtype=torch.float32)
            for i, c in enumerate(self.multilabel_classes):
                if c in sample.finding_labels:
                    vec[i] = 1.0
            return vec

        raise ValueError(f"Unsupported task type: {self.task}")

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]:
        sample = self.samples[idx]
        image_tensor = self.preprocessor(sample.image_path)
        label_tensor = self._get_label(sample)

        metadata = {
            "sample_id": sample.sample_id,
            "dataset": sample.dataset,
            "body_part": sample.body_part,
            "view": sample.view,
            "is_abnormal": sample.is_abnormal,
            "has_bbox": sample.has_bbox,
            "has_mask": sample.has_mask,
            "split": sample.split,
        }

        return image_tensor, label_tensor, metadata


def xray_collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]]):
    """Collate batch tensors and preserve metadata list without strict collation errors on None fields."""
    images = torch.stack([item[0] for item in batch], dim=0)
    labels = torch.stack([item[1] for item in batch], dim=0)
    metas = [item[2] for item in batch]
    return images, labels, metas


def create_xray_dataloader(
    dataset: NormalizedXRayDataset,
    batch_size: int = 16,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    """Helper factory for DataLoader instances with safe metadata handling."""
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=xray_collate_fn,
    )
