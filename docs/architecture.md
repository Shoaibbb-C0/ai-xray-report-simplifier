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
- Engineered strictly in **PyTorch**.
- Modularized into:
  - `datasets/`: Dataset manifest management and loaders.
  - `preprocessing/`: Standardized image pipeline (letterboxing, grayscale conversion, tensor normalization).
  - `training/`: Native training loops and loss formulations.
  - `evaluation/`: Clinical benchmark evaluation scripts (ROC-AUC, specificity, sensitivity).
  - `inference/`: Forward-pass runtime routines.
  - `saved_models/`: In-house model weights (`.pth` files, git-ignored).
  - `learning/`: Preserved initial experimental code.
