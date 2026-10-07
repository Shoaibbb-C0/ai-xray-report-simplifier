# Dataset Provenance, Licensing & Data Use Guidelines

This document tracks the provenance, canonical sources, licensing terms, and acquisition statuses for all radiograph datasets integrated into or targeted by the **AI X-Ray Project**.

---

## 1. FracAtlas
- **Dataset Name**: FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs
- **Provider**: Department of Computer Science & Engineering, United International University, Dhaka, Bangladesh / Published in *Nature Scientific Data* (2023)
- **Canonical Source**: [https://doi.org/10.6084/m9.figshare.22363012.v7](https://doi.org/10.6084/m9.figshare.22363012.v7)
- **Intended Use**: In-house training for bone fracture classification, anatomical body-part routing, localization, and educational visualization.
- **License**: **Creative Commons Attribution 4.0 International (CC BY 4.0)**
  - Unrestricted academic and commercial use with attribution.
- **Citation**:
  > Abedeen, I., Rahman, M.A., Prottyasha, F.Z. et al. *FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs.* Sci Data 10, 521 (2023). https://doi.org/10.1038/s41597-023-02432-4
- **Download Status**: **Downloaded and Verified** (~322 MB, 4,083 valid radiographs).
- **Date Acquired**: October 2026.
- **Local Storage Path**: `ml/datasets/raw/fracatlas/` (strictly excluded from Git).

---

## 2. Stanford MURA
- **Dataset Name**: MURA: Large Dataset for Abnormality Detection in Musculoskeletal Radiographs
- **Provider**: Stanford ML Group / Stanford Medicine
- **Canonical Source**: [https://stanfordmlgroup.github.io/competitions/mura/](https://stanfordmlgroup.github.io/competitions/mura/)
- **Intended Use**: Musculoskeletal abnormality screening and multi-class upper-extremity anatomical recognition (elbow, finger, forearm, hand, humerus, shoulder, wrist).
- **License**: **Stanford MURA Research Data Use Agreement**
  - Requires user registration and acceptance of research-only terms before acquiring raw images.
- **Citation**:
  > Rajpurkar, P. et al. *MURA: Large Dataset for Abnormality Detection in Musculoskeletal Radiographs.* arXiv:1712.06957 (2017).
- **Download Status**: **Pending User Manual Download** (requires user agreement).
- **Target Local Path**: `ml/datasets/raw/mura/`

---

## 3. NIH ChestX-ray14
- **Dataset Name**: NIH ChestX-ray14 (Hospital-scale Chest X-ray Database)
- **Provider**: National Institutes of Health (NIH) Clinical Center
- **Canonical Source**: [https://nihcc.app.box.com/v/ChestXray-NIHCC](https://nihcc.app.box.com/v/ChestXray-NIHCC)
- **Intended Use**: Chest radiograph branch, multi-label thoracic finding classification.
- **License**: **Open Commons / Public Domain Dedication**
  - Clinical caution: Finding labels were generated via text mining of radiology reports using NLP and contain ~10% extraction noise.
- **Citation**:
  > Wang, X. et al. *ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks.* IEEE CVPR, 2017.
- **Download Status**: **Pending Manual Download** (~42 GB full image archive).
- **Target Local Path**: `ml/datasets/raw/chestxray14/`

---

## 4. VinDr-SpineXR
- **Dataset Name**: VinDr-SpineXR: An Annotated Medical Image Dataset for Spine Radiograph Interpretation
- **Provider**: VinBigdata / PhysioNet
- **Canonical Source**: [https://physionet.org/content/vindr-spinexr/1.0.0/](https://physionet.org/content/vindr-spinexr/1.0.0/)
- **Intended Use**: Spine radiograph lesion detection, vertebral classification, and localization.
- **License**: **PhysioNet Credentialed Health Data License 1.5.0 (Strictly Restricted)**
  - Requires formal CITI human-subjects training certification, account verification, and signed Data Use Agreement (DUA).
- **Citation**:
  > Nguyen, H.T., Pham, H.H., Nguyen, L.T. et al. *VinDr-SpineXR: A large annotated medical image dataset for spine radiograph classification.* PhysioNet (2021).
- **Download Status**: **Restricted** (requires manual credentialing).
- **Target Local Path**: `ml/datasets/raw/vindr_spine/`

---

## Critical Repository Protection Policy
**Raw datasets, medical image binaries, and personal health data must NEVER be committed to Git.**
All dataset directories under `ml/datasets/raw/` and processed cached images are enforced as ignored in `.gitignore`. Only schema code, adapter interfaces, and reproducible JSON split manifests are version-controlled.
