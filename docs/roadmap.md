# Project Stages & Development Roadmap

## Two Locked Product Features

### Feature 1: Smart X-Ray Analysis
- User uploads an X-ray / radiograph.
- System validates whether the uploaded image is a usable radiograph.
- Automatically identifies the anatomical body region.
- Routes the image to the corresponding custom-trained model.
- Detects supported abnormalities with confidence scoring.
- Generates a patient-friendly visual explanation paired with non-jargon explanatory text.
- Provides optional comparison alongside the original image.

### Feature 2: My X-Ray Map
- Patient radiograph history organized over an interactive anatomical human-body map.
- Clicking any body region reveals historical scans, dates, findings, and explanations.
- Longitudinal tracking and scan-over-scan progression comparisons.

---

## Phased Execution Roadmap

### Stage 1: Foundation (Current Stage)
- [x] Establish clean, production-ready directory structure.
- [x] Build minimal Next.js frontend shell (JavaScript + Tailwind CSS).
- [x] Build FastAPI backend foundation with `/health` and service layer architecture.
- [x] Organize ML pipeline directories (`datasets`, `preprocessing`, `training`, `evaluation`, `inference`, `saved_models`, `learning`).
- [x] Preserve existing learning experiments and verify execution.
- [x] Set up comprehensive testing, environment templates, and strict `.gitignore`.

### Stage 2: Dataset Curation & Preprocessing Pipeline
- Curate public research datasets (e.g. CheXpert, MURA).
- Build PyTorch dataset loaders with aspect-ratio-preserving padding.
- Implement data augmentation and normalization routines.

### Stage 3: In-House Model Training & Validation
- Train body part classifier using PyTorch.
- Train pathology screening networks on curated datasets.
- Generate calibration curves, ROC-AUC benchmarks, and validation reports.
- Export production model weights to `ml/saved_models/`.

### Stage 4: Service Integration & Feature Implementation
- Connect FastAPI backend to live PyTorch inference engine.
- Wire frontend upload, routing, and simplified explanation views.
- Implement interactive SVG anatomical map for My X-Ray Map.

### Stage 5: End-to-End Testing & Review
- Comprehensive unit and integration test coverage across frontend and backend.
- Performance profiling and clinical safety review.
