"""Tests for PyTorch Dataset and DataLoader batch generation."""

import pytest
import torch
from ml.datasets.adapters.fracatlas import FracAtlasAdapter
from ml.datasets.registry import RAW_DATASETS_DIR
from ml.datasets.torch_dataset import NormalizedXRayDataset, create_xray_dataloader


@pytest.fixture(scope="module")
def fracatlas_samples():
    """Module-level fixture providing loaded FracAtlas samples."""
    adapter = FracAtlasAdapter(RAW_DATASETS_DIR / "fracatlas")
    if not adapter.is_available():
        pytest.skip("Local FracAtlas dataset is missing; copy it to ml/datasets/raw/fracatlas")
    samples = adapter.load_manifest()
    assert len(samples) > 0
    return samples


def test_pytorch_dataset_sample_item(fracatlas_samples):
    """Verify single __getitem__ yields [1, 224, 224] tensor, label, and metadata."""
    dataset = NormalizedXRayDataset(fracatlas_samples[:10], task="binary")
    assert len(dataset) == 10

    img_tensor, label_tensor, meta = dataset[0]

    assert isinstance(img_tensor, torch.Tensor)
    assert img_tensor.shape == (1, 224, 224)
    assert img_tensor.dtype == torch.float32

    assert isinstance(label_tensor, torch.Tensor)
    assert label_tensor.shape == (1,)
    assert label_tensor.dtype == torch.float32
    assert label_tensor.item() in (0.0, 1.0)

    assert "sample_id" in meta
    assert "body_part" in meta


def test_dataloader_batch_generation(fracatlas_samples):
    """Verify DataLoader retrieves batches of shape [B, 1, 224, 224] with no NaN/Inf."""
    batch_size = 4
    dataset = NormalizedXRayDataset(fracatlas_samples[:16], task="binary")
    loader = create_xray_dataloader(dataset, batch_size=batch_size, shuffle=False)

    batch_imgs, batch_labels, batch_meta = next(iter(loader))

    assert batch_imgs.shape == (batch_size, 1, 224, 224)
    assert batch_imgs.dtype == torch.float32
    assert not torch.isnan(batch_imgs).any()
    assert not torch.isinf(batch_imgs).any()

    assert batch_labels.shape == (batch_size, 1)
    assert batch_labels.dtype == torch.float32


def test_body_part_classification_task(fracatlas_samples):
    """Verify body_part classification task yields class index tensor."""
    dataset = NormalizedXRayDataset(fracatlas_samples[:10], task="body_part")
    img_tensor, label_tensor, _ = dataset[0]

    assert label_tensor.dtype == torch.int64
    assert 0 <= label_tensor.item() < len(NormalizedXRayDataset.BODY_PART_CLASSES)
