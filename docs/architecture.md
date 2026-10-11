# System Architecture

## Overview
The AI X-Ray Project is structured as a decoupled, multi-tier system engineered for patient-centric radiograph education and screening support:

```
┌────────────────────────────────────────────────────────┐
│                   Next.js Frontend                     │
│         (Pure JavaScript + Tailwind CSS)               │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / JSON
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
│             (/api/v1 Router, Service Layer)            │
└───────────────────────────┬────────────────────────────┘
                            │ In-Memory Pipeline Call
                            ▼
┌────────────────────────────────────────────────────────┐
│                   PyTorch ML Engine                    │
│   (Letterboxing, Normalization, Custom Model Infer)    │
└────────────────────────────────────────────────────────┘
```

## Subsystems

### 1. Presentation Tier (`frontend/`)
- Built with **Next.js** using standard **JavaScript** (no TypeScript).
- Styled with **Tailwind CSS** adopting a minimalist, high-clarity medical aesthetic.
- Responsible for file upload validation, interactive human body mapping, and presenting simplified, reassuring visual explanations.

### 2. Application Tier (`backend/`)
- Built with **FastAPI** on Python 3.14.
- Exposes RESTful endpoints (`/health`, `/api/v1/...`).
- Validates payload schemas, manages request lifecycle, coordinates error states, and dispatches requests to the ML service layer.

### 3. Machine Learning Tier (`ml/`)
- Engineered strictly in **PyTorch** running fully local without third-party generative/vision APIs.
- Modularized into:
  - `datasets/`: Dataset manifest management and loaders. Includes `splits/validator/` and `splits/body_part/` deterministic, leakage-free splits.
  - `models/`: Custom PyTorch architectures:
    - `XRayValidatorCNN` (101,553 params): Binary radiograph vs non-radiograph classifier with uncertainty rejection band (`p < 0.35` -> NON_XRAY, `0.35 <= p <= 0.65` -> UNCERTAIN, `p > 0.65` -> X_RAY).
    - `BodyPartClassifierCNN` (105,908 params): 4-class anatomical classifier (Hand, Leg, Hip, Shoulder) with weighted CrossEntropyLoss and confidence-based UNKNOWN rejection (`max_prob < 0.60` -> UNKNOWN).
  - `preprocessing/`: Standardized image pipeline (letterboxing, grayscale conversion, tensor normalization to `[1, 224, 224]`).
  - `training/`: Native training loops, early stopping, and metric calculation (`engine.py`, `train_validator.py`, `train_body_part.py`).
  - `evaluation/`: Clinical benchmark evaluation scripts (`evaluate_validator.py`, `evaluate_body_part.py`).
  - `inference/`: `Stage3InferencePipeline` and `predict_stage3.py` CLI routing engine.
  - `saved_models/`: In-house model weights (`best_validator.pt`, `best_body_part.pt`, git-ignored).
  - `learning/`: Preserved initial experimental code.

