"""Cascaded Stage 4 End-to-End Inference Pipeline.

Connects:
1. XRayPreprocessor
2. Stage 3 Model A: X-Ray Validator (rejects NON_XRAY and UNCERTAIN)
3. Stage 3 Model B: Body-Part Classifier (rejects UNKNOWN anatomy)
4. Stage 4 Model C: Fracture Classifier (evaluates FRACTURE, NO_FRACTURE, UNCERTAIN)

Follows strict medical safety standards:
- Explicit rejection of non-radiographs
- Clear quarantine of ambiguous/uncertain inputs
- Strictly limits abnormality findings to FRACTURE (no invented diseases)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import time
from typing import Any, Dict, Optional, Union
from PIL import Image
import torch

from ml.inference.fracture_classifier import FractureInferenceEngine
from ml.inference.stage3_pipeline import Stage3InferencePipeline
from ml.models.body_part_classifier import BodyPartClassifierCNN
from ml.models.fracture_classifier import FractureClassifierCNN
from ml.models.xray_validator import XRayValidatorCNN
from ml.preprocessing.pipeline import XRayPreprocessor

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def compute_file_sha256(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class Stage4InferencePipeline:
    """Integrated cascaded diagnostic-support pipeline for Stage 4."""

    SUPPORTED_BODY_PARTS = {"hand", "leg", "hip", "shoulder"}

    def __init__(
        self,
        validator_checkpoint: Optional[Path] = None,
        body_part_checkpoint: Optional[Path] = None,
        fracture_checkpoint: Optional[Path] = None,
        threshold_report_path: Optional[Path] = None,
        device: str = "cpu",
    ) -> None:
        self.device = device
        self.stage3 = Stage3InferencePipeline(
            validator_checkpoint=validator_checkpoint,
            body_part_checkpoint=body_part_checkpoint,
            device=device,
        )
        self.fracture_engine = FractureInferenceEngine(
            checkpoint_path=fracture_checkpoint,
            threshold_report_path=threshold_report_path,
            device=device,
        )

    def get_metadata(self) -> Dict[str, Any]:
        """Returns provenance metadata and SHA256 hashes for all pipeline models."""
        st3_meta = self.stage3.get_metadata()
        fracture_sha = compute_file_sha256(self.fracture_engine.ckpt_path)

        return {
            "device": self.device,
            "models": {
                "validator": {
                    "checkpoint": str(self.stage3.val_ckpt_path),
                    "sha256": st3_meta["validator"]["sha256"],
                    "thresholds": st3_meta["validator"]["thresholds"],
                },
                "body_part": {
                    "checkpoint": str(self.stage3.bp_ckpt_path),
                    "sha256": st3_meta["body_part"]["sha256"],
                    "unknown_threshold": st3_meta["body_part"]["unknown_threshold"],
                    "supported_classes": list(self.SUPPORTED_BODY_PARTS),
                },
                "fracture": {
                    "checkpoint": str(self.fracture_engine.ckpt_path),
                    "sha256": fracture_sha,
                    "decision_threshold": self.fracture_engine.threshold,
                    "uncertainty_band": [self.fracture_engine.lower_bound, self.fracture_engine.upper_bound],
                },
            },
        }

    def predict(self, image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
        """Executes full Stage 4 cascaded pipeline on an input image."""
        start_time = time.perf_counter()

        # Step 1 & 2: Run Stage 3 validation and anatomical routing
        st3_res = self.stage3.predict(image_input)
        val_decision = st3_res["validator"]["decision"]
        val_conf = st3_res["validator"]["confidence"]

        result_payload: Dict[str, Any] = {
            "xray_validation": {
                "result": val_decision.lower(),
                "confidence": val_conf,
                "probability": st3_res["validator"]["probability"],
            },
            "body_part": None,
            "abnormality": None,
            "pipeline_status": None,
            "models": {
                "validator": "XRayValidatorCNN",
                "body_part": "BodyPartClassifierCNN",
                "fracture": "FractureClassifierCNN",
            },
            "timings_ms": {},
        }

        # Gate 1: Non-X-Ray rejection
        if val_decision == "NON_XRAY":
            result_payload["pipeline_status"] = "REJECTED_NON_XRAY"
            result_payload["rejection_reason"] = "Input image was determined not to be an interpretable medical X-ray radiograph."
            result_payload["timings_ms"]["total"] = round((time.perf_counter() - start_time) * 1000, 2)
            return result_payload

        # Gate 2: Inconclusive radiograph validation
        if val_decision == "UNCERTAIN":
            result_payload["pipeline_status"] = "REJECTED_UNCERTAIN_VALIDATION"
            result_payload["rejection_reason"] = "Radiograph validation is borderline/inconclusive. Analysis safely suspended."
            result_payload["timings_ms"]["total"] = round((time.perf_counter() - start_time) * 1000, 2)
            return result_payload

        # Extract Stage 3 Body Part findings
        bp_pred = st3_res.get("body_part", {}) or {}
        bp_class = bp_pred.get("predicted_anatomy", "unknown").lower()
        bp_conf = bp_pred.get("confidence", 0.0)

        result_payload["body_part"] = {
            "result": bp_class,
            "confidence": bp_conf,
            "probabilities": bp_pred.get("class_probabilities", {}),
        }

        # Gate 3: Unsupported or rejected anatomical region
        if bp_class not in self.SUPPORTED_BODY_PARTS or bp_class == "unknown":
            result_payload["pipeline_status"] = "REJECTED_UNSUPPORTED_ANATOMY"
            result_payload["rejection_reason"] = f"Anatomical region '{bp_class}' is outside the supported musculoskeletal fracture scope."
            result_payload["timings_ms"]["total"] = round((time.perf_counter() - start_time) * 1000, 2)
            return result_payload

        # Step 3: Run Model C (Fracture Classifier)
        t_frac_start = time.perf_counter()
        frac_res = self.fracture_engine.predict(image_input)
        t_frac_end = time.perf_counter()

        result_payload["abnormality"] = {
            "task": "fracture",
            "result": frac_res["result"],
            "status_description": frac_res["status_description"],
            "confidence": frac_res["confidence"],
            "fracture_probability": frac_res["fracture_probability"],
            "thresholds": frac_res["thresholds"],
        }
        result_payload["pipeline_status"] = "ANALYSIS_COMPLETE"

        total_time_ms = (time.perf_counter() - start_time) * 1000
        frac_time_ms = (t_frac_end - t_frac_start) * 1000
        result_payload["timings_ms"] = {
            "fracture_classifier_alone_ms": round(frac_time_ms, 2),
            "total_pipeline_ms": round(total_time_ms, 2),
        }

        return result_payload
