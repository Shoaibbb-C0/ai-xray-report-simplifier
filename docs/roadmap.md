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

### Stage 4: Abnormality Detection & Specialized Model (Completed — 71% Project Target)
- [x] Train in-house Model C: Fracture Classifier (`FractureClassifierCNN`, 995,169 parameters, 0.7336 ROC-AUC, 0.5151 PR-AUC).
- [x] Handle strong class imbalance via training-set weighted BCE loss (`pos_weight = 4.811`).
- [x] Implement conservative training radiograph data augmentation with tensor caching.
- [x] Calibrate decision threshold (`0.35`) and clinical uncertainty band (`[0.23, 0.47]`) strictly on validation data.
- [x] Complete untouched test set evaluation with per-body-part performance and structured error analysis.
- [x] Complete FracAtlas localization annotation audit (719 annotated fracture images, 924 boxes) and Grad-CAM visualizer.
- [x] Build cascaded `Stage4InferencePipeline` with safety gates rejecting non-radiographs and unknown anatomy.
- [x] All 44 automated tests passing; frontend production build verified.

### Stage 5: Visual Explanation Engine (Completed — 79% Project Target)
- [x] Establish strict conceptual separation: Model Prediction vs Model Attention vs Explanatory Illustration.
- [x] Create original application-owned accessible SVG anatomical illustrations for Hand, Leg, Hip, Shoulder, and generic fallbacks.
- [x] Build deterministic, patient-safe `VisualExplanationEngine` with zero third-party commercial AI API dependencies.
- [x] Implement structured 8-state resolution (`VALID_XRAY_FRACTURE_SUSPECTED`, `VALID_XRAY_NO_FRACTURE_SIGNAL`, `VALID_XRAY_UNCERTAIN`, etc.).
- [x] Enforce Grad-CAM attention suppression for uncertain, non-radiograph, and unrecognized anatomy cases.
- [x] Maintain localization boundary: mark experimental bounding box heads as unverified and disable for patients.
- [x] Implement translation registry supporting English, Hindi, and Marathi with plain-language medical glossary.
- [x] Create reusable frontend components (`AnatomicalIllustration`, `EducationalComparison`, `ModelAttentionOverlay`, `ExplanationCard`, `LimitationNotice`).
- [x] Build development preview route (`/dev/explanations`) with 7 deterministic software fixtures.
- [x] All 57 automated tests passing; frontend production build verified.

### Stage 6: Database & Persistence Layer (Planned — Next Stage)
- Introduce Supabase backend for secure patient history and scan metadata storage.
- Implement structured database schema with row-level security (RLS).
- Store serializable Stage 5 explanation results alongside scan records.


