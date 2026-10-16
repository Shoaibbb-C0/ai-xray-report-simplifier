# Stage 5 — Visual Explanation Engine

## 1. Executive Summary & Purpose
Stage 5 introduces the project's **Visual Explanation Engine**, advancing overall project progress from **71% to 79%**. 

The engine converts raw multi-model ML outputs (`X-Ray Validator` $\to$ `Body-Part Classifier` $\to$ `Fracture Classifier`) into safe, understandable, structured visual explanations for patients without calling external commercial AI APIs (such as OpenAI, Gemini, or Claude).

---

## 2. Core Separation of Concepts
To prevent misleading clinical expectations or patient alarm, the engine enforces strict conceptual boundaries across three distinct modalities:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. MODEL PREDICTION                                                    │
│    Statistical likelihood of fracture (suspected / no signal /         │
│    uncertain) derived from Model C features.                           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ 2. MODEL ATTENTION (Grad-CAM)                                          │
│    Computational visualization of pixel features that influenced the   │
│    model. NOT an exact medical injury location.                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ 3. PATIENT EXPLANATORY ILLUSTRATION                                    │
│    Original, clean anatomical vector drawing showing what bone         │
│    continuity and fracture mean conceptually. NOT evidence from the    │
│    patient's specific radiograph.                                      │
└────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> A Grad-CAM attention heatmap is **NOT** a clinical fracture boundary.
> An educational illustration is **NOT** drawn at the patient's individual injury location.

---

## 3. Supported Scope & Anatomical Domains
* **Supported Pathology**: **Fracture Only** (Model C trained on FracAtlas).
* **Supported Anatomical Classes**:
  * `HAND` (Hand & Wrist)
  * `LEG` (Leg & Knee)
  * `HIP` (Hip & Pelvis)
  * `SHOULDER` (Shoulder & Clavicle)
* **Safe Fallback States**:
  * `MIXED`: Multi-region or transitional anatomy fallback
  * `UNKNOWN`: Unrecognized region routed to educational notice
  * `UNCERTAIN`: Low-confidence prediction routed to clinician review

---

## 4. Explanation Architecture & Result States
The engine deterministically maps the ML cascade outputs into one of 8 canonical states:

1. `VALID_XRAY_FRACTURE_SUSPECTED`: Valid radiograph + high-confidence fracture probability ($P \ge 0.47$).
2. `VALID_XRAY_NO_FRACTURE_SIGNAL`: Valid radiograph + low fracture probability ($P < 0.23$).
3. `VALID_XRAY_UNCERTAIN`: Valid radiograph within calibrated uncertainty band $[0.23, 0.47]$.
4. `BODY_PART_UNKNOWN`: Valid radiograph of anatomy outside supported categories.
5. `NON_XRAY`: File rejected at Stage 3 Validator gate.
6. `XRAY_VALIDATION_UNCERTAIN`: Input ambiguity at Validator gate.
7. `MODEL_UNAVAILABLE`: Model weights or inference service offline.
8. `ERROR`: Malformed input or runtime exception.

---

## 5. Patient-Safe Language Engine & Phrasing Rules
All patient-facing text is generated deterministically using structured templates and translation keys:

* **Positive Finding**:
  > *"The model detected features that may be associated with a fracture in the {body region}."*
* **Negative Finding**:
  > *"The model did not detect strong fracture-related features in this image. This does not rule out a fracture. A clinician should interpret the X-ray together with symptoms and examination findings."*
* **Uncertain State**:
  > *"The model could not make a confident classification from this image."*
* **Safety & Uncertainty Policy**:
  > *"The system routes low-confidence predictions to an uncertain state to reduce overconfident classifications; false positives and false negatives remain possible."*

### Forbidden Language Policy
Patient text strictly prohibits definitive diagnostic phrasing:
* ❌ `"You have a fracture."`
* ❌ `"Confirmed fracture."`
* ❌ `"No fracture exists."`
* ❌ `"Your exact fracture location."`
* ❌ `"Clinically validated diagnosis."`

---

## 6. Curated Anatomical Illustration System
Original application-owned SVG vector artwork is stored under `assets/anatomy/` and mirrored in `frontend/public/assets/anatomy/`:
* `hand/`: `hand_neutral.svg`, `hand_fracture_educational.svg`
* `leg/`: `leg_neutral.svg`, `leg_fracture_educational.svg`
* `hip/`: `hip_neutral.svg`, `hip_fracture_educational.svg`
* `shoulder/`: `shoulder_neutral.svg`, `shoulder_fracture_educational.svg`
* `common/`: `generic_neutral.svg`, `generic_fracture_educational.svg`, `non_xray.svg`, `uncertain.svg`

### Accessibility & Visual Safety
* Every SVG features semantic `<title>`, `<desc>`, `role="img"`, and `aria-label`.
* Fracture concept SVGs include an explicit prominent badge: **"Example illustration — Not patient's X-ray"**.
* High contrast, no information conveyed by color alone.

---

## 7. Model Attention (Grad-CAM) Safety Rules
* Generated via `FractureGradCAM` on Block 5 conv features (`features.16`) of `FractureClassifierCNN`.
* Blended in-memory into an RGBA thermal overlay and returned as a Base64 data URI (no permanent file storage).
* **Strict Suppression**: Grad-CAM is strictly disabled whenever the result is `UNCERTAIN`, `NON_XRAY`, `BODY_PART_UNKNOWN`, or `NO_FRACTURE_SIGNAL`.

---

## 8. Localization Model Boundary
* The experimental single-box bounding-box head from Stage 4 remains **unverified** for clinical diagnostic usage.
* In Stage 5, `localization.available = False` and `localization.status = "experimental_unverified"` are strictly enforced. Bounding boxes are not rendered to patients.

---

## 9. Translation Architecture & Multilingual Readiness
A centralized translation registry in [`ml/explanation/translations.py`](file:///c:/Users/ADMIN/OneDrive/Desktop/Shoaib/Projects/ai-xray-report-simplifier/ml/explanation/translations.py) decouples application logic from user-facing copy:
* **English (`en`)**: Complete primary localization.
* **Hindi (`hi`)**: Curated medical and finding translations.
* **Marathi (`mr`)**: Curated medical and finding translations.

---

## 10. Frontend Components
Modular React components in `frontend/components/explanation/`:
* `AnatomicalIllustration.jsx`: Accessible vector guide with educational notice.
* `EducationalComparison.jsx`: Side-by-side normal vs simulated fracture concept.
* `ModelAttentionOverlay.jsx`: Grad-CAM overlay viewer with opacity slider and disclaimer banner.
* `ExplanationCard.jsx`: Structured 4-part patient card.
* `LimitationNotice.jsx`: High-visibility clinical disclaimer banner.
* `GlossaryDrawer.jsx`: Expandable plain-language medical glossary.
* Developer Preview Route: Accessible at `/dev/explanations` with 7 interactive software fixtures.

---

## 11. Supabase Compatibility (Stage 6 Readiness)
Every explanation result produced by `VisualExplanationEngine.explain()` conforms to `ExplanationResult` (Pydantic v2). It cleanly serializes via `.model_dump()` and `.model_dump_json()` for storage in Supabase scan records during Stage 6 without requiring schema restructuring.
