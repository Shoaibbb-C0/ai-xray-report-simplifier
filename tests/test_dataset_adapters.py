"""Tests for Dataset Adapters (FracAtlas real data, and MURA/Chest/Spine contract fixtures)."""

import csv
from pathlib import Path
import pytest

from ml.datasets.adapters.fracatlas import FracAtlasAdapter
from ml.datasets.adapters.mura import MURAAdapter
from ml.datasets.adapters.chestxray14 import ChestXray14Adapter
from ml.datasets.adapters.vindr_spine import VinDrSpineAdapter
from ml.datasets.registry import RAW_DATASETS_DIR


def test_fracatlas_adapter_on_real_data():
    """Verify FracAtlas adapter parses the real downloaded dataset."""
    adapter = FracAtlasAdapter(RAW_DATASETS_DIR / "fracatlas")
    if not adapter.is_available():
        pytest.skip("Local FracAtlas dataset is missing; copy it to ml/datasets/raw/fracatlas")
    assert adapter.is_available()

    samples = adapter.load_manifest()
    assert len(samples) == 4083

    # Check fracture and non-fracture instances
    fractured_samples = [s for s in samples if s.is_abnormal]
    non_fractured_samples = [s for s in samples if not s.is_abnormal]

    assert len(fractured_samples) == 719
    assert len(non_fractured_samples) == 3364

    # Verify anatomical body parts are recognized
    body_parts = {s.body_part for s in samples}
    assert {"hand", "leg", "hip", "shoulder"}.issubset(body_parts)


def test_mura_adapter_missing_state(tmp_path):
    """Verify MURA adapter reports unavailable on empty directory."""
    empty_dir = tmp_path / "mura_empty"
    empty_dir.mkdir()
    adapter = MURAAdapter(empty_dir)
    assert not adapter.is_available()
    assert adapter.load_manifest() == []


def test_mura_adapter_with_fixtures(tmp_path):
    """Verify MURA adapter correctly parses labeled study structures."""
    mura_dir = tmp_path / "MURA-v1.1"
    mura_dir.mkdir()

    # Create dummy CSV files
    study_csv = mura_dir / "train_labeled_studies.csv"
    with open(study_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["MURA-v1.1/train/XR_WRIST/patient00001/study1_positive/", "1"])
        writer.writerow(["MURA-v1.1/train/XR_HAND/patient00002/study1_negative/", "0"])

    paths_csv = mura_dir / "train_image_paths.csv"
    with open(paths_csv, mode="w", newline="", encoding="utf-8") as f:
        f.write("MURA-v1.1/train/XR_WRIST/patient00001/study1_positive/image1.png\n")
        f.write("MURA-v1.1/train/XR_HAND/patient00002/study1_negative/image1.png\n")

    adapter = MURAAdapter(tmp_path)
    assert adapter.is_available()

    samples = adapter.load_manifest()
    assert len(samples) == 2

    wrist_sample = next(s for s in samples if s.body_part == "wrist")
    assert wrist_sample.patient_id == "patient00001"
    assert wrist_sample.is_abnormal is True
    assert "musculoskeletal_abnormality" in wrist_sample.finding_labels

    hand_sample = next(s for s in samples if s.body_part == "hand")
    assert hand_sample.patient_id == "patient00002"
    assert hand_sample.is_abnormal is False


def test_chestxray14_adapter_multilabel_fixture(tmp_path):
    """Verify ChestX-ray14 parses pipe-separated multi-label findings."""
    csv_path = tmp_path / "Data_Entry_2017_v2020.csv"
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictReader
        headers = ["Image Index", "Finding Labels", "Follow-up #", "Patient ID", "Patient Age", "Patient Gender", "View Position"]
        csv_w = csv.DictWriter(f, fieldnames=headers)
        csv_w.writeheader()
        csv_w.writerow({
            "Image Index": "00000001_000.png",
            "Finding Labels": "Cardiomegaly|Effusion",
            "Follow-up #": "0",
            "Patient ID": "1",
            "Patient Age": "58",
            "Patient Gender": "M",
            "View Position": "PA",
        })
        csv_w.writerow({
            "Image Index": "00000002_000.png",
            "Finding Labels": "No Finding",
            "Follow-up #": "0",
            "Patient ID": "2",
            "Patient Age": "60",
            "Patient Gender": "F",
            "View Position": "AP",
        })

    adapter = ChestXray14Adapter(tmp_path)
    assert adapter.is_available()
    samples = adapter.load_manifest()
    assert len(samples) == 2

    abnormal = samples[0]
    assert abnormal.body_part == "chest"
    assert abnormal.view == "PA"
    assert abnormal.is_abnormal is True
    assert set(abnormal.finding_labels) == {"Cardiomegaly", "Effusion"}

    normal = samples[1]
    assert normal.is_abnormal is False
    assert normal.finding_labels == []


def test_vindr_spine_missing_state(tmp_path):
    """Verify VinDr-Spine adapter reports unavailable on empty directory."""
    empty_dir = tmp_path / "vindr_empty"
    empty_dir.mkdir()
    adapter = VinDrSpineAdapter(empty_dir)
    assert not adapter.is_available()
    assert adapter.load_manifest() == []
