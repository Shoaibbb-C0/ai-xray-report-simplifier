"""Integrated Stage 3 Inference Pipeline.

Connects:
1. XRayPreprocessor (letterboxing, normalization, [1, 224, 224] tensor)
2. Model A: X-Ray Validator (binary classification + uncertainty band)
3. Model B: Body-Part Classifier (4-class anatomical model + unknown/rejection threshold)

Provides single entrypoint method for clean routing.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any, Union, Optional
import torch
from PIL import Image, ImageFile

from ml.models.xray_validator import XRayValidatorCNN
from ml.models.body_part_classifier import BodyPartClassifierCNN
from ml.preprocessing.pipeline import XRayPreprocessor

ImageFile.LOAD_TRUNCATED_IMAGES = True

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_CKPT = PROJECT_ROOT / "ml" / "saved_models" / "stage3" / "validator" / "best_validator.pt"
BODY_PART_CKPT = PROJECT_ROOT / "ml" / "saved_models" / "stage3" / "body_part" / "best_body_part.pt"


def compute_file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class Stage3InferencePipeline:
    """End-to-end inference engine for Stage 3 validation and anatomical routing."""

    def __init__(
        self,
        validator_checkpoint: Optional[Path] = None,
        body_part_checkpoint: Optional[Path] = None,
        device: str = "cpu",
        validator_lower: float = 0.35,
        validator_upper: float = 0.65,
        body_part_unknown_threshold: float = 0.60,
    ) -> None:
        self.device = torch.device(device)
        self.val_lower = validator_lower
        self.val_upper = validator_upper
        self.bp_unknown_thresh = body_part_unknown_threshold

        self.preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)

        self.val_ckpt_path = validator_checkpoint or VALIDATOR_CKPT
        self.bp_ckpt_path = body_part_checkpoint or BODY_PART_CKPT

        self.validator_model = XRayValidatorCNN().to(self.device)
        self.body_part_model = BodyPartClassifierCNN(num_classes=4).to(self.device)

        self._load_checkpoints()

    def _load_checkpoints(self) -> None:
        for checkpoint in (self.val_ckpt_path, self.bp_ckpt_path):
            if not Path(checkpoint).is_file():
                raise FileNotFoundError("Trained Stage 3 model checkpoint is unavailable")
        if self.val_ckpt_path.exists():
            ckpt = torch.load(self.val_ckpt_path, map_location=self.device)
            self.validator_model.load_state_dict(ckpt["model_state_dict"])
            self.validator_model.eval()

        if self.bp_ckpt_path.exists():
            ckpt = torch.load(self.bp_ckpt_path, map_location=self.device)
            self.body_part_model.load_state_dict(ckpt["model_state_dict"])
            self.body_part_model.eval()

    def get_metadata(self) -> Dict[str, Any]:
        """Returns model hashes and version metadata."""
        meta = {
            "device": str(self.device),
            "validator": {
                "checkpoint": str(self.val_ckpt_path),
                "sha256": compute_file_sha256(self.val_ckpt_path) if self.val_ckpt_path.exists() else None,
                "thresholds": {"lower": self.val_lower, "upper": self.val_upper},
            },
            "body_part": {
                "checkpoint": str(self.bp_ckpt_path),
                "sha256": compute_file_sha256(self.bp_ckpt_path) if self.bp_ckpt_path.exists() else None,
                "unknown_threshold": self.bp_unknown_thresh,
                "classes": BodyPartClassifierCNN.CLASS_NAMES,
            },
        }
        return meta

    def predict(self, image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
        """Executes full Stage 3 inference pipeline on a single image."""
        tensor = self.preprocessor(image_input).unsqueeze(0).to(self.device)

        # 1. Validator Inference
        with torch.no_grad():
            val_logit = self.validator_model(tensor)
            val_prob = float(torch.sigmoid(val_logit).cpu().item())

        if val_prob < self.val_lower:
            validator_decision = "NON_XRAY"
            validator_status = "rejected"
        elif val_prob > self.val_upper:
            validator_decision = "X_RAY"
            validator_status = "accepted"
        else:
            validator_decision = "UNCERTAIN"
            validator_status = "uncertain"

        result: Dict[str, Any] = {
            "validator": {
                "decision": validator_decision,
                "status": validator_status,
                "probability": round(val_prob, 4),
                "confidence": round(val_prob if val_prob >= 0.5 else 1.0 - val_prob, 4),
            },
            "body_part": None,
            "pipeline_status": "complete",
        }

        # If rejected as non-xray, we do not force body-part prediction
        if validator_decision == "NON_XRAY":
            result["pipeline_status"] = "rejected_non_xray"
            return result

        if validator_decision == "UNCERTAIN":
            result["pipeline_status"] = "uncertain_xray"
            return result

        # 2. Body-Part Inference (for accepted or uncertain x-rays)
        with torch.no_grad():
            bp_logits = self.body_part_model(tensor)
            bp_probs = torch.softmax(bp_logits, dim=1).cpu().numpy()[0]

        classes = BodyPartClassifierCNN.CLASS_NAMES
        class_probs = {cls_name: round(float(bp_probs[i]), 4) for i, cls_name in enumerate(classes)}

        best_idx = int(bp_probs.argmax())
        best_class = classes[best_idx]
        best_conf = float(bp_probs[best_idx])

        if best_conf < self.bp_unknown_thresh:
            bp_decision = "UNKNOWN"
            is_rejected = True
        else:
            bp_decision = best_class
            is_rejected = False

        result["body_part"] = {
            "predicted_anatomy": bp_decision,
            "confidence": round(best_conf, 4),
            "top_candidate": best_class,
            "is_rejected_as_unknown": is_rejected,
            "class_probabilities": class_probs,
        }

        if validator_decision == "UNCERTAIN":
            result["pipeline_status"] = "uncertain_xray"
        elif bp_decision == "UNKNOWN":
            result["pipeline_status"] = "unknown_anatomy"
        else:
            result["pipeline_status"] = "success"

        return result
