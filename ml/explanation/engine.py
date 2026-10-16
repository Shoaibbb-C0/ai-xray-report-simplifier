"""Visual Explanation Engine for Stage 5.

Transforms raw Stage 3 and Stage 4 ML cascade outputs into structured,
patient-safe, educational explanations without calling external AI APIs.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
from PIL import Image
import torch

from ml.explanation.schema import (
    AnalysisStatus,
    AttentionExplanation,
    BodyPartId,
    BodyRegionInfo,
    ExplanationResult,
    FindingInfo,
    FindingState,
    LocalizationInfo,
    VisualExplanation,
)
from ml.explanation.glossary import get_glossary
from ml.explanation.translations import t
from ml.explanation.visual_mapper import BODY_PART_DISPLAY_NAMES, resolve_illustration


class VisualExplanationEngine:
    """Deterministic, patient-safe visual explanation generator."""

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._gradcam = None
        self._fracture_model = None

    def _get_gradcam(self):
        """Lazy-load Grad-CAM instance only if attention visualization is requested."""
        if self._gradcam is None:
            from ml.models.fracture_classifier import FractureClassifierCNN
            from ml.evaluation.gradcam import FractureGradCAM

            ckpt_path = Path("ml/saved_models/stage4/fracture_classifier/best_fracture_classifier.pt")
            if not ckpt_path.exists():
                return None
            model = FractureClassifierCNN().to(self.device)
            ckpt = torch.load(ckpt_path, map_location=self.device, weights_only=False)
            state_dict = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
            model.load_state_dict(state_dict)
            model.eval()
            self._fracture_model = model
            self._gradcam = FractureGradCAM(model)
        return self._gradcam

    def generate_attention_overlay(
        self,
        image_input: Union[str, Path, Image.Image, torch.Tensor],
    ) -> Optional[str]:
        """Compute Grad-CAM heatmap and return transparent PNG data URI (base64)."""
        try:
            gradcam = self._get_gradcam()
            if gradcam is None:
                return None

            from ml.preprocessing.pipeline import XRayPreprocessor

            preprocessor = XRayPreprocessor(target_size=(224, 224))

            if isinstance(image_input, torch.Tensor):
                tensor = image_input
            else:
                tensor = preprocessor.preprocess(image_input)

            if tensor.ndim == 3:
                tensor = tensor.unsqueeze(0)
            tensor = tensor.to(self.device)
            tensor.requires_grad = True

            # Generate 224x224 float heatmap in [0, 1]
            heatmap = gradcam.generate_heatmap(tensor)

            # Convert heatmap to RGBA transparent colormap (plasma-like thermal overlay)
            # Active regions: amber/red with high alpha; cold regions: transparent
            h, w = heatmap.shape
            rgba = np.zeros((h, w, 4), dtype=np.uint8)

            # Color mapping: warm gradient (yellow -> orange -> crimson)
            r = np.clip(heatmap * 255 * 1.2, 0, 255).astype(np.uint8)
            g = np.clip((1.0 - np.abs(heatmap - 0.5) * 2.0) * 180, 0, 180).astype(np.uint8)
            b = np.clip((1.0 - heatmap) * 60, 0, 60).astype(np.uint8)

            # Alpha mapping: transparent below 0.15 threshold, scaling smoothly up to 180
            alpha = np.where(heatmap < 0.15, 0, np.clip((heatmap - 0.15) / 0.85 * 180, 0, 180)).astype(np.uint8)

            rgba[:, :, 0] = r
            rgba[:, :, 1] = g
            rgba[:, :, 2] = b
            rgba[:, :, 3] = alpha

            overlay_img = Image.fromarray(rgba, mode="RGBA")
            buf = io.BytesIO()
            overlay_img.save(buf, format="PNG")
            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64_str}"
        except Exception:
            return None

    def explain(
        self,
        cascade_output: Dict[str, Any],
        image_input: Optional[Union[str, Path, Image.Image, torch.Tensor]] = None,
        generate_attention: bool = False,
        lang: str = "en",
    ) -> ExplanationResult:
        """Translate Stage 3 + Stage 4 cascade result into a structured explanation."""
        xray_val = cascade_output.get("xray_validation", {})
        body_part_res = cascade_output.get("body_part", {})
        abnormality_res = cascade_output.get("abnormality", {})

        is_xray = bool(
            xray_val.get("is_xray", False)
            or str(xray_val.get("result", "")).lower() in ("x_ray", "xray", "valid")
        )
        val_conf = float(xray_val.get("confidence", 0.0))

        raw_body_part = str(
            body_part_res.get("predicted_class")
            or body_part_res.get("result")
            or "unknown"
        ).lower()
        body_part_conf = float(body_part_res.get("confidence", 0.0))

        fracture_result = abnormality_res.get("result", "not_analyzed") if abnormality_res else "not_analyzed"
        fracture_prob = float(abnormality_res.get("fracture_probability", 0.0)) if abnormality_res else None
        fracture_conf = float(abnormality_res.get("confidence", 0.0)) if abnormality_res else None

        # Canonical Body Part mapping
        if raw_body_part in ("hand", "wrist", "hand_wrist"):
            body_id = BodyPartId.HAND
            is_supported_anatomy = True
        elif raw_body_part in ("leg", "knee", "foot", "ankle"):
            body_id = BodyPartId.LEG
            is_supported_anatomy = True
        elif raw_body_part in ("hip", "pelvis"):
            body_id = BodyPartId.HIP
            is_supported_anatomy = True
        elif raw_body_part in ("shoulder", "clavicle"):
            body_id = BodyPartId.SHOULDER
            is_supported_anatomy = True
        elif raw_body_part == "mixed":
            body_id = BodyPartId.MIXED
            is_supported_anatomy = True
        else:
            body_id = BodyPartId.UNKNOWN
            is_supported_anatomy = False

        body_label = BODY_PART_DISPLAY_NAMES.get(body_id, "Unrecognized Region")
        body_info = BodyRegionInfo(
            id=body_id,
            label=body_label,
            is_supported=is_supported_anatomy,
            confidence=body_part_conf,
        )

        # -------------------------------------------------------------
        # Determine High-Level Analysis State
        # -------------------------------------------------------------
        if not is_xray:
            status = AnalysisStatus.NON_XRAY
            finding_state = FindingState.NOT_ANALYZED
        elif val_conf < 0.60:
            status = AnalysisStatus.XRAY_VALIDATION_UNCERTAIN
            finding_state = FindingState.NOT_ANALYZED
        elif not is_supported_anatomy:
            status = AnalysisStatus.BODY_PART_UNKNOWN
            finding_state = FindingState.UNSUPPORTED
        elif fracture_result == "uncertain":
            status = AnalysisStatus.VALID_XRAY_UNCERTAIN
            finding_state = FindingState.UNCERTAIN
        elif fracture_result == "fracture":
            status = AnalysisStatus.VALID_XRAY_FRACTURE_SUSPECTED
            finding_state = FindingState.SUSPECTED
        elif fracture_result == "no_fracture":
            status = AnalysisStatus.VALID_XRAY_NO_FRACTURE_SIGNAL
            finding_state = FindingState.NO_SIGNAL
        elif cascade_output.get("pipeline_status") == "MODEL_UNAVAILABLE":
            status = AnalysisStatus.MODEL_UNAVAILABLE
            finding_state = FindingState.NOT_ANALYZED
        else:
            status = AnalysisStatus.ERROR
            finding_state = FindingState.NOT_ANALYZED

        finding_info = FindingInfo(
            id="fracture",
            label="Bone Fracture",
            state=finding_state,
            probability=fracture_prob,
            confidence=fracture_conf,
        )

        # -------------------------------------------------------------
        # Visual Asset Resolution
        # -------------------------------------------------------------
        is_non_xray = (status == AnalysisStatus.NON_XRAY)
        is_xray_uncertain = (status == AnalysisStatus.XRAY_VALIDATION_UNCERTAIN)
        visual_info = resolve_illustration(
            body_part=body_id,
            finding_state=finding_state,
            is_non_xray=is_non_xray,
            is_xray_uncertain=is_xray_uncertain,
        )

        # -------------------------------------------------------------
        # Model Attention (Grad-CAM)
        # -------------------------------------------------------------
        # STRICT SAFETY RULE:
        # Grad-CAM is ONLY generated when valid radiograph + fracture suspected.
        # Disabled for UNCERTAIN, NON_XRAY, and UNKNOWN anatomy.
        attention_info = AttentionExplanation(
            available=False,
            type="gradcam",
            is_exact_localization=False,
            clinical_localization=False,
        )

        if generate_attention and status == AnalysisStatus.VALID_XRAY_FRACTURE_SUSPECTED and image_input is not None:
            overlay_b64 = self.generate_attention_overlay(image_input)
            if overlay_b64:
                attention_info.available = True
                attention_info.overlay_base64 = overlay_b64

        # -------------------------------------------------------------
        # Deterministic Patient-Safe Text Generation
        # -------------------------------------------------------------
        limitations: List[str] = [
            t("limitation.uncertainty_routing", lang=lang),
            t("limitation.anatomy_scope", lang=lang),
        ]

        # 1. WHAT THIS X-RAY IS ABOUT
        purpose_key = f"anatomy.purpose.{body_id.value}"
        what_this_test_checks = t(purpose_key, lang=lang, default=t("anatomy.purpose.unknown", lang=lang))

        # 2. MODEL FINDING & SUMMARY
        if status == AnalysisStatus.VALID_XRAY_FRACTURE_SUSPECTED:
            summary = t("finding.fracture.suspected", lang=lang)
            what_the_result_means = (
                f"The model detected features that may be associated with a fracture in the {body_label.lower()}. "
                "This indicates potential bone discontinuity or alignment disruption requiring clinician review."
            )
            next_step_message = t("next_step.suspected", lang=lang)
            limitations.insert(0, t("limitation.educational", lang=lang))

        elif status == AnalysisStatus.VALID_XRAY_NO_FRACTURE_SIGNAL:
            summary = t("finding.fracture.no_signal", lang=lang)
            clarification = t("finding.negative_clarification", lang=lang)
            what_the_result_means = f"{summary} {clarification}"
            next_step_message = t("next_step.no_signal", lang=lang)
            limitations.insert(0, t("limitation.false_negative", lang=lang))

        elif status == AnalysisStatus.VALID_XRAY_UNCERTAIN:
            summary = t("finding.fracture.uncertain", lang=lang)
            what_the_result_means = (
                "The model could not make a confident classification from this image. "
                "The visual features fall within a borderline zone, so automated scoring is withheld to prevent misleading conclusions."
            )
            next_step_message = t("next_step.uncertain", lang=lang)

        elif status == AnalysisStatus.BODY_PART_UNKNOWN:
            summary = t("validation.unknown_body_part", lang=lang)
            what_the_result_means = (
                "Automated fracture detection is strictly calibrated for supported body regions "
                "(Hand, Leg, Hip, Shoulder). Because this region is unrecognized or unsupported, no fracture analysis was run."
            )
            next_step_message = "Please upload an X-ray of a supported limb or joint."

        elif status == AnalysisStatus.NON_XRAY:
            summary = t("validation.non_xray", lang=lang)
            what_the_result_means = (
                "The input image failed radiographic validation criteria (contrast, structure, or content) "
                "and was not recognized as a medical X-ray."
            )
            next_step_message = t("next_step.invalid", lang=lang)

        elif status == AnalysisStatus.XRAY_VALIDATION_UNCERTAIN:
            summary = t("validation.uncertain", lang=lang)
            what_the_result_means = (
                "The input image could not be verified with adequate confidence as a medical radiograph."
            )
            next_step_message = t("next_step.invalid", lang=lang)

        elif status == AnalysisStatus.MODEL_UNAVAILABLE:
            summary = t("validation.model_unavailable", lang=lang)
            what_the_result_means = "The specialized abnormality model is currently offline or undergoing maintenance."
            next_step_message = "Please try again later or contact the clinical system administrator."

        else:
            summary = "An unexpected error occurred during image processing."
            what_the_result_means = "The image could not be processed completely through the analysis cascade."
            next_step_message = "Please check the file format and try uploading again."

        # Model versions audit
        model_versions = cascade_output.get("models", {
            "validator": "ValidatorCNN_Stage3",
            "body_part": "BodyPartClassifierCNN_Stage3",
            "fracture_classifier": "FractureClassifierCNN_Stage4",
        })

        # Translation keys mapping for frontend localization
        translation_keys = {
            "status": status.value,
            "body_part": body_id.value,
            "finding_state": finding_state.value,
            "summary_key": f"finding.fracture.{finding_state.value}" if finding_state.value in ("suspected", "no_signal", "uncertain") else f"validation.{status.value.lower()}",
            "purpose_key": purpose_key,
        }

        return ExplanationResult(
            analysis_status=status,
            body_part=body_info,
            finding=finding_info,
            summary=summary,
            what_this_test_checks=what_this_test_checks,
            what_the_result_means=what_the_result_means,
            next_step_message=next_step_message,
            limitations=limitations,
            visual=visual_info,
            attention=attention_info,
            localization=LocalizationInfo(),
            medical_glossary=get_glossary(lang=lang),
            model_versions=model_versions,
            language=lang,
            translation_keys=translation_keys,
        )
