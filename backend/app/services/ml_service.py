"""Service abstraction for future in-house ML model inference.

This service defines the architectural boundary between the FastAPI web layer
and the underlying PyTorch inference engine.

IMPORTANT:
Per Stage 1 specifications, no pre-trained weights or fake predictions exist.
This service exposes model readiness state and contracts for future model
loading and evaluation routines.
"""

from typing import Dict, Any, Optional


class MLServiceError(Exception):
    """Base exception for ML service failures."""
    pass


class ModelNotLoadedError(MLServiceError):
    """Raised when inference is requested before trained weights are loaded."""
    pass


class MLInferenceService:
    """Interface for managing in-house trained PyTorch model lifecycles and inference."""

    def __init__(self) -> None:
        self._models_loaded: bool = False
        self._active_models: Dict[str, Any] = {}

    @property
    def is_ready(self) -> bool:
        """Indicates whether trained models are loaded into memory."""
        return self._models_loaded

    def get_service_status(self) -> Dict[str, Any]:
        """Returns the readiness state and metadata of the ML subsystem."""
        return {
            "ready": self.is_ready,
            "loaded_models_count": len(self._active_models),
            "engine": "PyTorch",
            "active_models": list(self._active_models.keys()),
        }

    def load_model(self, model_name: str, checkpoint_path: str) -> None:
        """Placeholder for loading a trained PyTorch model checkpoint.
        
        Will be implemented during the model training and serialization stage.
        """
        # TODO (Stage 3): Implement torch.load and state_dict assignment to architecture
        raise NotImplementedError("Model loading will be implemented once in-house training is complete.")

    def run_inference(self, image_tensor: Any) -> Dict[str, Any]:
        """Placeholder for running forward-pass inference.
        
        Strictly raises ModelNotLoadedError in Stage 1 to prevent placeholder predictions.
        """
        if not self._models_loaded:
            raise ModelNotLoadedError("No trained PyTorch models are currently loaded.")
        raise NotImplementedError("Inference pipeline will be wired in future stages.")


ml_service = MLInferenceService()
