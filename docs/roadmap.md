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

### Stage 1: Foundation (Completed)
- [x] Establish clean, production-ready directory structure.
- [x] Build minimal Next.js frontend shell (JavaScript + Tailwind CSS).
- [x] Build FastAPI backend foundation with `/health` and service layer architecture.
- [x] Organize ML pipeline directories (`datasets`, `preprocessing`, `training`, `evaluation`, `inference`, `saved_models`, `learning`).
- [x] Preserve existing learning experiments and verify execution.
- [x] Set up comprehensive testing, environment templates, and strict `.gitignore`.

### Stage 2: Dataset Curation & Preprocessing Pipeline (Completed)
- [x] Curate FracAtlas and integrate multi-dataset adapters (MURA, NIH ChestX-ray14, VinDr-SpineXR).
- [x] Build PyTorch dataset loaders with aspect-ratio-preserving padding.
- [x] Implement duplicate audit and perceptual hash clustering to eliminate leakage.
- [x] Create deterministic, leak-free train/val/test splits.

### Stage 3: X-Ray Validator + Body-Part Classifier (Completed)
- [x] Train in-house Model A: X-Ray Validator (`XRayValidatorCNN`, 98.71% test accuracy, 98.64% balanced accuracy, 0.9988 ROC-AUC).
- [x] Establish validation-derived uncertainty threshold band (`[0.35, 0.65]`) rejecting 100% of zero-shot OOD negative imagery.
- [x] Train in-house Model B: Body-Part Classifier (`BodyPartClassifierCNN`, 83.34% test macro-F1, 87.32% overall accuracy across Hand, Leg, Hip, Shoulder).
- [x] Implement UNKNOWN rejection policy on mixed/ambiguous anatomy (`max_prob < 0.60`).
- [x] Export checkpoints to `ml/saved_models/stage3/` and verify checksums.
- [x] Implement end-to-end `Stage3InferencePipeline` and `predict_stage3.py` CLI.


### Stage 4: Service Integration & Feature Implementation
- Connect FastAPI backend to live PyTorch inference engine.
- Wire frontend upload, routing, and simplified explanation views.
- Implement interactive SVG anatomical map for My X-Ray Map.

### Stage 5: End-to-End Testing & Review
- Comprehensive unit and integration test coverage across frontend and backend.
- Performance profiling and clinical safety review.
