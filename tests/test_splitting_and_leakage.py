"""Tests for deterministic dataset splitting and leakage detection."""

import pytest
from ml.datasets.adapters.base import NormalizedSample
from ml.datasets.splitting import DataLeakageError, DatasetSplitter, check_data_leakage


def test_deterministic_split_consistency():
    """Verify same seed produces identical split assignments."""
    samples = [
        NormalizedSample(sample_id=f"sample_{i}", dataset="test", image_path=f"img_{i}.png", patient_id=f"patient_{i // 2}")
        for i in range(100)
    ]

    splitter_1 = DatasetSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=123)
    splits_1 = splitter_1.split_samples(samples)

    splitter_2 = DatasetSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=123)
    splits_2 = splitter_2.split_samples(samples)

    assert [s.sample_id for s in splits_1["train"]] == [s.sample_id for s in splits_2["train"]]
    assert [s.sample_id for s in splits_1["validation"]] == [s.sample_id for s in splits_2["validation"]]
    assert [s.sample_id for s in splits_1["test"]] == [s.sample_id for s in splits_2["test"]]


def test_patient_level_isolation_no_leakage():
    """Verify samples from the same patient are strictly isolated to one split."""
    # Create 30 patients, each having 3 different scans
    samples = []
    for p_idx in range(30):
        for s_idx in range(3):
            samples.append(
                NormalizedSample(
                    sample_id=f"p{p_idx}_s{s_idx}",
                    dataset="test",
                    image_path=f"/path/p{p_idx}_{s_idx}.jpg",
                    patient_id=f"patient_{p_idx}",
                )
            )

    splitter = DatasetSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42)
    splits = splitter.split_samples(samples)

    # Check zero overlap
    check_data_leakage(splits)

    train_pts = {s.patient_id for s in splits["train"]}
    val_pts = {s.patient_id for s in splits["validation"]}
    test_pts = {s.patient_id for s in splits["test"]}

    assert len(train_pts.intersection(val_pts)) == 0
    assert len(train_pts.intersection(test_pts)) == 0
    assert len(val_pts.intersection(test_pts)) == 0


def test_leakage_detector_raises_loudly():
    """Verify check_data_leakage raises DataLeakageError upon artificial overlap."""
    sample_a = NormalizedSample(sample_id="s1", dataset="test", image_path="a.png", patient_id="p1")
    sample_b = NormalizedSample(sample_id="s2", dataset="test", image_path="b.png", patient_id="p2")
    sample_leak = NormalizedSample(sample_id="s3", dataset="test", image_path="c.png", patient_id="p1")

    # Patient p1 is in both train and test!
    leaky_splits = {
        "train": [sample_a],
        "validation": [sample_b],
        "test": [sample_leak],
    }

    with pytest.raises(DataLeakageError) as exc_info:
        check_data_leakage(leaky_splits)

    assert "Patient ID leakage" in str(exc_info.value)
