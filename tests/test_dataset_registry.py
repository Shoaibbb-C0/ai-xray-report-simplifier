"""Tests for Dataset Registry and availability tracking."""

from dataclasses import replace
from ml.datasets.registry import DATASET_REGISTRY, get_dataset_metadata, list_datasets


def test_registry_contains_required_datasets():
    """Verify all four target datasets are registered with complete metadata."""
    expected = {"fracatlas", "mura", "chestxray14", "vindr_spine"}
    assert expected.issubset(set(DATASET_REGISTRY.keys()))


def test_registry_metadata_contracts():
    """Verify registry entries conform to contract requirements."""
    for dataset_id, meta in DATASET_REGISTRY.items():
        assert meta.dataset_id == dataset_id
        assert len(meta.supported_anatomy) > 0
        assert len(meta.task_types) > 0
        assert meta.license_name
        assert meta.canonical_source.startswith("http")
        assert meta.citation


def test_availability_reflects_actual_filesystem_state(tmp_path):
    """Verify live availability flags reflect local filesystem."""
    # Exercise both states without requiring a previous machine's ignored data.
    fracatlas_meta = replace(get_dataset_metadata("fracatlas"), raw_dir=tmp_path / "fracatlas")
    assert fracatlas_meta.availability_state == "not_downloaded"
    fracatlas_meta.raw_dir.mkdir()
    (fracatlas_meta.raw_dir / "dataset.csv").touch()
    assert fracatlas_meta.availability_state == "not_downloaded"
    for folder in ("Fractured", "Non_fractured"):
        (fracatlas_meta.raw_dir / "images" / folder).mkdir(parents=True)
    assert fracatlas_meta.availability_state == "available"

    # MURA has not been downloaded yet
    mura_meta = replace(get_dataset_metadata("mura"), raw_dir=tmp_path / "mura")
    assert mura_meta is not None
    assert mura_meta.availability_state == "not_downloaded"

    # ChestX-ray14 has not been downloaded yet
    chest_meta = replace(get_dataset_metadata("chestxray14"), raw_dir=tmp_path / "chestxray14")
    assert chest_meta is not None
    assert chest_meta.availability_state == "not_downloaded"

    # VinDr-Spine is restricted-access PhysioNet data
    spine_meta = replace(get_dataset_metadata("vindr_spine"), raw_dir=tmp_path / "vindr_spine")
    assert spine_meta is not None
    assert spine_meta.availability_state == "restricted"


def test_list_datasets_summary():
    """Verify list_datasets returns well-formed summary objects."""
    datasets = list_datasets()
    assert len(datasets) == 4
    for d in datasets:
        assert "dataset_id" in d
        assert "availability" in d
        assert "supported_anatomy" in d
        assert "license" in d
