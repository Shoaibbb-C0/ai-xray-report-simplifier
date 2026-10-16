"""Inference interface for Model C: Fracture Classifier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from PIL import Image
import torch

from ml.models.fracture_classifier import FractureClassifierCNN
from ml.preprocessing.pipeline import XRayPreprocessor

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CKPT = PROJECT_ROOT / "ml" / "saved_models" / "stage4" / "fracture_classifier" / "best_fracture_classifier.pt"
DEFAULT_THRESHOLD_REPORT = PROJECT_ROOT / "ml" / "saved_models" / "stage4" / "fracture_classifier" / "threshold_report.json"


class FractureInferenceEngine:
    """Production inference engine for Model C (Fracture Classifier)."""

    def __init__(
        self,
        checkpoint_path: Optional[Path] = None,
        threshold_report_path: Optional[Path] = None,
        device: str = "cpu",
    ) -> None:
        self.device = torch.device(device)
        self.ckpt_path = Path(checkpoint_path) if checkpoint_path else DEFAULT_CKPT
        self.threshold_path = Path(threshold_report_path) if threshold_report_path else DEFAULT_THRESHOLD_REPORT

        self.preprocessor = XRayPreprocessor(target_size=(224, 224), mean=0.5, std=0.5)
        self.model = FractureClassifierCNN().to(self.device)

        self.threshold = 0.35
        self.lower_bound = 0.23
        self.upper_bound = 0.47

        self._load_thresholds()
        self._load_checkpoint()

    def _load_thresholds(self) -> None:
        if self.threshold_path.exists():
            try:
                with open(self.threshold_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    calibrated = data.get("calibrated_policy", {})
                    self.threshold = calibrated.get("decision_threshold", self.threshold)
                    policy = calibrated.get("uncertainty_policy", {})
                    self.lower_bound = policy.get("lower_bound", self.lower_bound)
                    self.upper_bound = policy.get("upper_bound", self.upper_bound)
            except Exception:
                pass

    def _load_checkpoint(self) -> None:
        if self.ckpt_path.exists():
            ckpt = torch.load(self.ckpt_path, map_location=self.device)
            self.model.load_state_dict(ckpt["model_state_dict"])
            self.model.eval()

    def predict(self, image_input: Union[str, Path, Image.Image]) -> Dict[str, Any]:
        """Runs single-image fracture classification."""
        tensor = self.preprocessor(image_input).unsqueeze(0).to(self.device)

        self.model.eval()
        with torch.no_grad():
            logit = self.model(tensor)
            prob = float(torch.sigmoid(logit).squeeze().cpu().item())

        # Tri-state decision logic
        if prob < self.lower_bound:
            result = "no_fracture"
            status_text = "no features associated with fracture detected"
        elif prob > self.upper_bound:
            result = "fracture"
            status_text = "model detected features associated with fracture"
        else:
            result = "uncertain"
            status_text = "indeterminate radiograph features (inconclusive / borderline)"

        # Clinical reassurance confidence (distance from decision boundary)
        confidence = round(prob if prob >= 0.5 else (1.0 - prob), 4)

        return {
            "task": "fracture",
            "result": result,
            "status_description": status_text,
            "fracture_probability": round(prob, 4),
            "confidence": confidence,
            "thresholds": {
                "decision": self.threshold,
                "uncertainty_band": [self.lower_bound, self.upper_bound],
            },
        }
