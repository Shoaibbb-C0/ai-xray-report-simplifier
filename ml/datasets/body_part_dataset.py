"""Dataset class for 4-class Body-Part classification.

Classes:
0: hand
1: leg
2: hip
3: shoulder
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import ImageFile

from ml.datasets.adapters.base import NormalizedSample
from ml.preprocessing.pipeline import XRayPreprocessor

ImageFile.LOAD_TRUNCATED_IMAGES = True

BODY_PART_CLASSES = ["hand", "leg", "hip", "shoulder"]
BODY_PART_TO_IDX = {name: i for i, name in enumerate(BODY_PART_CLASSES)}


class BodyPartDataset(Dataset):
    """Consumes body part manifests and produces (image_tensor, class_idx, metadata)."""

    def __init__(
        self,
        samples: List[NormalizedSample],
        preprocessor: XRayPreprocessor,
    ) -> None:
        self.samples = samples
        self.preprocessor = preprocessor

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, Any]]:
        sample = self.samples[idx]
        image_tensor = self.preprocessor(sample.image_path)
        bp = (sample.body_part or "unknown").lower()
        if bp not in BODY_PART_TO_IDX:
            raise ValueError(f"Unknown or unmapped body part '{bp}' for sample {sample.sample_id}")
        class_idx = BODY_PART_TO_IDX[bp]
        label_tensor = torch.tensor(class_idx, dtype=torch.int64)

        metadata = {
            "sample_id": sample.sample_id,
            "dataset": sample.dataset,
            "body_part": sample.body_part,
            "view": sample.view,
            "is_abnormal": sample.is_abnormal,
            "split": sample.split,
        }
        return image_tensor, label_tensor, metadata


def create_body_part_dataloader(
    dataset: BodyPartDataset,
    batch_size: int = 64,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    def collate_fn(batch):
        images = torch.stack([item[0] for item in batch], dim=0)
        labels = torch.stack([item[1] for item in batch], dim=0)
        metas = [item[2] for item in batch]
        return images, labels, metas

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_fn,
    )
