"""Grad-CAM (Gradient-weighted Class Activation Mapping) for Model C feature attention inspection.

NOTE & MEDICAL SAFETY NOTICE:
Grad-CAM heatmaps visualize model activation and visual feature attention.
Grad-CAM is NOT a calibrated medical lesion detector or exact fracture boundary locator.
Heatmaps are provided exclusively for ML explainability, debugging, and sanity checks.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from ml.models.fracture_classifier import FractureClassifierCNN
from ml.preprocessing.pipeline import XRayPreprocessor


class FractureGradCAM:
    """Computes Grad-CAM attention heatmaps from the final convolutional feature layer."""

    def __init__(self, model: FractureClassifierCNN, target_layer: Optional[torch.nn.Module] = None) -> None:
        self.model = model
        self.target_layer = target_layer or model.get_last_conv_layer()
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None

        self._hook_handles = []
        self._register_hooks()

    def _register_hooks(self) -> None:
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        h1 = self.target_layer.register_forward_hook(forward_hook)
        h2 = self.target_layer.register_full_backward_hook(backward_hook)
        self._hook_handles.extend([h1, h2])

    def generate_heatmap(self, input_tensor: torch.Tensor) -> np.ndarray:
        """Generates a 2D float32 [0.0, 1.0] attention heatmap for a [1, 1, H, W] tensor."""
        self.model.eval()
        self.model.zero_grad()

        # Forward pass
        logits = self.model(input_tensor)
        score = logits[0, 0]

        # Backward pass for gradient of fracture logit
        score.backward()

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Gradients or activations were not captured by hooks.")

        # Global average pooling of gradients: weights alpha_k
        alpha = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # [1, C, 1, 1]
        weighted_act = torch.sum(alpha * self.activations, dim=1, keepdim=True)  # [1, 1, H', W']
        cam = F.relu(weighted_act)  # Only positive influence

        # Upsample to match input spatial dimensions (224, 224)
        _, _, h, w = input_tensor.shape
        cam_upsampled = F.interpolate(cam, size=(h, w), mode="bilinear", align_corners=False)
        cam_np = cam_upsampled.squeeze().cpu().numpy()

        # Normalize to [0.0, 1.0]
        max_val = np.max(cam_np)
        if max_val > 0:
            cam_np = cam_np / max_val
        else:
            cam_np = np.zeros_like(cam_np)

        return cam_np.astype(np.float32)

    def remove_hooks(self) -> None:
        """Removes registered PyTorch forward and backward hooks."""
        for h in self._hook_handles:
            h.remove()
        self._hook_handles.clear()
