# Datasets Directory

## Purpose
This directory houses scripts, manifests, and dataset loaders for public medical X-ray datasets.

## Storage Policy
- **Never commit raw medical images, DICOM files, or large archives to Git.**
- Raw downloads should reside locally in `datasets/raw/` (ignored by `.gitignore`).
- Preprocessed tensors or split caches should reside in `datasets/processed/` (ignored by `.gitignore`).
- Only lightweight metadata (CSV manifests, download scripts, split indices) may be tracked.

## Planned Datasets
- Chest Radiographs: NIH ChestX-ray14, CheXpert, or PadChest
- Musculoskeletal Radiographs: Stanford MURA (Musculoskeletal Radiographs)
