# Datasets Module — AI X-Ray Project

## Overview
This module manages medical radiograph datasets for our in-house PyTorch models. All raw medical images and binary archives are strictly excluded from version control via `.gitignore`.

## Registered Datasets & Live Status

| Dataset ID | Full Name | Status | Anatomy | Source / License |
| :--- | :--- | :--- | :--- | :--- |
| `fracatlas` | **FracAtlas** | **AVAILABLE** | Hand, Leg, Hip, Shoulder | [Figshare (CC BY 4.0)](https://doi.org/10.6084/m9.figshare.22363012.v7) |
| `mura` | **MURA** | `not_downloaded` | Elbow, Finger, Forearm, Hand, Humerus, Shoulder, Wrist | Stanford Research Agreement |
| `chestxray14` | **NIH ChestX-ray14** | `not_downloaded` | Chest | NIH Clinical Center Open Commons |
| `vindr_spine` | **VinDr-SpineXR** | `restricted` | Spine | PhysioNet Credentialed DUA |

See [`docs/dataset-licenses.md`](../../docs/dataset-licenses.md) for full provenance, citations, and licensing terms.

---

## Directory Architecture

```
ml/datasets/
├── raw/                         # Local raw downloads (STRICTLY GIT-IGNORED)
│   ├── fracatlas/               # FracAtlas archive & extracted images
│   ├── mura/                    # Target for user manual placement
│   ├── chestxray14/             # Target for chest archive
│   └── vindr_spine/             # Target for credentialed PhysioNet files
│
├── adapters/                    # Standardized ingestion adapters
│   ├── base.py                  # NormalizedSample schema and BaseDatasetAdapter
│   ├── fracatlas.py             # Active adapter for FracAtlas
│   ├── mura.py                  # Adapter for Stanford MURA
│   ├── chestxray14.py           # Multi-label adapter for NIH ChestX-ray14
│   └── vindr_spine.py           # Interface for VinDr-SpineXR
│
├── splits/                      # Reproducible JSON/CSV split manifests
│   ├── fracatlas/               # Deterministic train/val/test splits (seed=42)
│   │   ├── train.json           # 2,858 samples (70%)
│   │   ├── validation.json      # 612 samples (15%)
│   │   └── test.json            # 613 samples (15%)
│   └── eda_report.json          # Machine-readable dataset health summary
│
├── registry.py                  # Central registry with live availability checks
├── validation.py                # Image integrity, corruption, and health checks
├── splitting.py                 # Deterministic splitting & leak protection
├── torch_dataset.py             # NormalizedXRayDataset & DataLoader factory
└── eda.py                       # CLI EDA summary generation tool
```

---

## Running Dataset Validation & EDA

To generate the comprehensive dataset health report:
```powershell
python ml/datasets/eda.py
```
Or for a specific dataset:
```powershell
python ml/datasets/eda.py --dataset fracatlas
```

## Running Splitting and Leakage Checks
```powershell
pytest tests/test_splitting_and_leakage.py -v
```
