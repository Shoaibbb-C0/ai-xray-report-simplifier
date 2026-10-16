# Stage 4 — Abnormality Detection & Specialized Model (Fracture Classifier)

## 1. Stage 4 Purpose & Scope
Stage 4 introduces the platform's first dedicated diagnostic-support pathology model: **Model C — Fracture Classifier** (`FractureClassifierCNN`).

> [!IMPORTANT]
> **Diagnostic Boundary**: Model C is explicitly trained and evaluated for **musculoskeletal fracture abnormality detection** within the supported FracAtlas data distribution (Hand, Leg, Hip, Shoulder). It is **NOT** a universal radiograph diagnostic model and does not detect or infer other pathologies (such as pneumonia, tumors, arthritis, dislocations, infections, osteoporosis, or scoliosis).

---

## 2. Dataset & Leakage-Safe Manifest Audit

### Raw FracAtlas Data Distribution
- **Total Images**: 4,083
- **Fractured Images**: 719 (17.61%)
- **Non-Fractured Images**: 3,364 (82.39%)
- **Hardware/Implant Scans**: 99
- **Multiscan Scans**: 396

### Anatomical Breakdown
| Anatomy | Total Samples | Fracture Count | Non-Fracture Count | Fracture Prevalence |
| :--- | :--- | :--- | :--- | :--- |
| **Leg** | 2,124 | 212 | 1,912 | 9.98% |
| **Hand** | 1,281 | 381 | 900 | 29.74% |
| **Mixed** | 398 | 106 | 292 | 26.63% |
| **Hip** | 179 | 10 | 169 | 5.59% |
| **Shoulder** | 101 | 10 | 91 | 9.90% |

### Leakage-Safe Splits (`fracatlas_v2`)
Splits enforce duplicate-cluster isolation to prevent data leakage:
- **Train Set**: 2,859 samples (492 fractured, 2,367 non-fractured)
- **Validation Set**: 611 samples (114 fractured, 497 non-fractured)
- **Test Set**: 613 samples (113 fractured, 500 non-fractured)

### Class Imbalance Strategy
Class imbalance ratio calculated strictly from the **training set**:
$$\text{pos\_weight} = \frac{N_{\text{neg}}}{N_{\text{pos}}} = \frac{2367}{492} = 4.8110$$
Applied directly to `torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([4.8110]))`. Validation and test distributions remain completely natural.

---

## 3. Model Architecture (`FractureClassifierCNN`)

Custom from-scratch PyTorch convolutional neural network designed for CPU-efficient musculoskeletal radiograph classification:
- **Input**: `[Batch, 1, 224, 224]` normalized float32 grayscale radiograph
- **Block 1**: Conv2d(1 -> 32, 3x3, pad=1) -> BatchNorm2d -> ReLU -> MaxPool2d(2, 2) `[112x112]`
- **Block 2**: Conv2d(32 -> 64, 3x3, pad=1) -> BatchNorm2d -> ReLU -> MaxPool2d(2, 2) `[56x56]`
- **Block 3**: Conv2d(64 -> 128, 3x3, pad=1) -> BatchNorm2d -> ReLU -> MaxPool2d(2, 2) `[28x28]`
- **Block 4**: Conv2d(128 -> 256, 3x3, pad=1) -> BatchNorm2d -> ReLU -> MaxPool2d(2, 2) `[14x14]`
- **Block 5**: Conv2d(256 -> 256, 3x3, pad=1) -> BatchNorm2d -> ReLU -> MaxPool2d(2, 2) `[7x7]`
- **Global Pooling**: AdaptiveAvgPool2d((1, 1))
- **Classifier Head**: Flatten -> Dropout(0.4) -> Linear(256 -> 64) -> ReLU -> Dropout(0.2) -> Linear(64 -> 1)
- **Output**: Single logit `[Batch, 1]` for BCEWithLogitsLoss
- **Total Parameters**: **995,169** (~0.995M)

---

## 4. Training Procedure & Augmentation

### Conservative Training Augmentation
Stochastic transformations applied exclusively during training:
- Random Horizontal Flip: $p = 0.5$
- Random Affine: rotation $\in [-8^\circ, +8^\circ]$, translation $\pm 4\%$, scaling $[0.96, 1.04]$
- Validation and test data undergo zero stochastic augmentation.

### Hyperparameters
- Optimizer: AdamW (`lr=1e-3`, `weight_decay=1e-4`)
- Scheduler: ReduceLROnPlateau (`mode='max'`, `factor=0.5`, `patience=2`)
- Early Stopping: `patience=4` monitored on validation F1
- Best Epoch: Epoch 5 (Validation F1 = 0.4646, ROC-AUC = 0.7687, PR-AUC = 0.5006)

---

## 5. Validation-Based Threshold Calibration & Uncertainty Policy

Threshold exploration conducted exclusively across the 611 validation samples:

| Threshold | F1 | Balanced Acc | Sensitivity (Recall) | Specificity | Precision | False Negatives |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.20 | 0.3657 | 0.6023 | 0.9298 | 0.2748 | 0.2274 | 8 |
| 0.30 | 0.4357 | 0.6720 | 0.7719 | 0.5721 | 0.2973 | 26 |
| **0.35** | **0.4570** | **0.6908** | **0.6754** | **0.7062** | **0.3453** | **37** |
| 0.40 | 0.4514 | 0.6775 | 0.5702 | 0.7847 | 0.3757 | 49 |
| 0.50 | 0.4309 | 0.6433 | 0.4474 | 0.8392 | 0.4158 | 63 |

### Selected Operating Point & Uncertainty Policy
- **Primary Decision Threshold**: `0.35`
- **Clinical Uncertainty Band**: `[0.23, 0.47]` (63.5% of validation cases categorized as borderline)
- **Inference Tri-State Rule**:
  - $p < 0.23 \rightarrow$ `NO_FRACTURE`
  - $0.23 \le p \le 0.47 \rightarrow$ `UNCERTAIN`
  - $p > 0.47 \rightarrow$ `FRACTURE`

---

## 6. Canonical Test Evaluation (Untouched Test Split)

Evaluated once on untouched test data (613 samples, 113 fractures, prevalence: 18.43%):

| Metric | Result | Description |
| :--- | :--- | :--- |
| **Accuracy** | 67.05% | Overall correct fraction |
| **Balanced Accuracy** | 65.76% | Arithmetic mean of sensitivity and specificity |
| **Sensitivity (Recall)** | **63.72%** | Fraction of actual fractures detected (72 / 113) |
| **Specificity** | **67.80%** | Fraction of healthy bones correctly identified (339 / 500) |
| **Precision** | 30.90% | Positive predictive value (72 / 233) |
| **F1 Score** | 0.4162 | Harmonic mean of precision and recall |
| **ROC-AUC** | **0.7336** | Area under Receiver Operating Characteristic curve |
| **PR-AUC** | **0.5151** | Area under Precision-Recall curve (vs 0.1843 random baseline) |
| **True Positives** | 72 | Confirmed fracture detections |
| **True Negatives** | 339 | Confirmed normal bones |
| **False Positives** | 161 | Non-fractured scans flagged for clinical review |
| **False Negatives** | 41 | Missed fractures |

### Confusion Matrix
```
                 Predicted Negative    Predicted Positive
Actual Negative         339                   161
Actual Positive          41                    72
```

---

## 7. Per-Body-Part Performance

| Anatomy | Support | Fractures | Precision | Recall (Sens.) | Specificity | F1 Score | Balanced Acc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HAND** | 192 | 59 | 35.54% | **72.88%** | 41.35% | 0.4778 | 57.12% |
| **LEG** | 323 | 34 | 22.09% | **55.88%** | 76.82% | 0.3167 | 66.35% |
| **MIXED** | 61 | 15 | 40.91% | **60.00%** | 71.74% | 0.4865 | 65.87% |
| **SHOULDER\*** | 16 | 3 | 25.00% | 33.33% | 76.92% | 0.2857 | 55.13% |
| **HIP\*** | 21 | 2 | 0.00% | 0.00% | 100.0% | 0.0000 | 50.00% |

*\*Statistically fragile: Hip (2 positive cases) and Shoulder (3 positive cases) have sample sizes too small in the test set to draw definitive regional conclusions.*

---

## 8. Error Analysis & Failure Patterns

- **False Negatives (41 missed fractures)**:
  - Hairline and non-displaced micro-fissures lacking prominent cortico-spatial displacement.
  - Hand radiographs ($n=16$) and leg radiographs ($n=15$) accounted for the majority.
  - Hardware was present in 7 false-negative cases where fixator density obscured bone detail.
- **False Positives (161 over-called scans)**:
  - Epiphyseal growth plates in pediatric/adolescent cases mimicking fracture lines.
  - Complex anatomical overlap (e.g. carpal bone stacking in lateral hand views).
- **Clinical Mitigation**:
  - The tri-state uncertainty band safely routes 65.9% of borderline scans to `UNCERTAIN`, prompting secondary review rather than emitting false certainty.

---

## 9. Localization Annotation Audit & Explainability

### FracAtlas Annotation Audit
- **Annotation Formats**: PASCAL VOC XML, YOLO TXT, COCO JSON
- **Total Annotated Fracture Images**: 719
- **Total Bounding Boxes**: 924
- **Single-Box Images**: 548 (76.2%)
- **Multi-Box Images**: 171 (23.8%, max 5 boxes per image)
- **Mean Relative Area**: 0.00662 (~0.66% of image frame, reflecting focal hairline targets)
- **Invalid Boxes**: 0

### Grad-CAM Attention Visualizer
Implemented via `ml/evaluation/gradcam.py` using Block 5 convolution activation gradients.
> [!CAUTION]
> **Grad-CAM Notice**: Activation maps depict neural network spatial attention for developer inspection. Grad-CAM is **NOT** a calibrated radiological lesion boundary detector.

---

## 10. Saved Model Checkpoint & Provenance

- **Path**: `ml/saved_models/stage4/fracture_classifier/best_fracture_classifier.pt`
- **File Size**: 11.42 MB (11,977,987 bytes)
- **SHA256**: `6696910128f3c0baf8d1d5725c83f4f85620be89511fda6400593cfc48e8ab31`
- **Git Status**: Binary checkpoint gitignored; tracked metadata in `training_config.json`, `history.json`, `threshold_report.json`, `evaluation_report.json`, and `model_metadata.json`.

---

## 11. Reproduction Commands

```powershell
# 1. Train Model C
python -m ml.training.train_fracture --epochs 6 --batch-size 64

# 2. Run Validation Threshold Calibration
python -m ml.evaluation.threshold_analysis

# 3. Evaluate on Untouched Test Set
python -m ml.evaluation.evaluate_fracture

# 4. Run CLI Inference on Any Image
python ml/inference/predict_stage4.py --image path/to/image.jpg

# 5. Run Stage 4 Automated Test Suite
pytest tests/test_stage4_models.py tests/test_stage4_inference.py -v
```
