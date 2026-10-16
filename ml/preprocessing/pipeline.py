"""Production radiograph image pre-processing pipeline."""

from pathlib import Path
from typing import Tuple, Union
import numpy as np
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import torch


class XRayPreprocessor:
    """Standardizes radiographs into calibrated PyTorch tensors.
    
    Operations:
    1. Safe image loading.
    2. Grayscale conversion ('L').
    3. Aspect-ratio-preserving letterboxing/padding (centered).
    4. Floating-point scaling to [0.0, 1.0].
    5. Normalization using mean and std.
    6. PyTorch tensor conversion [C, H, W] with C=1.
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        mean: float = 0.5,
        std: float = 0.5,
    ) -> None:
        self.target_size = target_size
        self.mean = mean
        self.std = std

    def letterbox_image(self, image: Image.Image) -> Image.Image:
        """Resize image preserving aspect ratio with zero-padded letterboxing."""
        target_w, target_h = self.target_size
        image_copy = image.copy()
        image_copy.thumbnail((target_w, target_h), Image.Resampling.BILINEAR)

        canvas = Image.new("L", (target_w, target_h), 0)
        x = (target_w - image_copy.width) // 2
        y = (target_h - image_copy.height) // 2
        canvas.paste(image_copy, (x, y))
        return canvas

    def load_image(self, image_input: Union[str, Path, Image.Image]) -> Image.Image:
        """Safely load and return a PIL Image."""
        if isinstance(image_input, Image.Image):
            return image_input
        path = Path(image_input)
        if not path.exists():
            parts = path.parts
            if "raw" in parts:
                raw_idx = parts.index("raw")
                rel_parts = parts[raw_idx + 1 :]
                from ml.datasets.registry import RAW_DATASETS_DIR
                candidate = RAW_DATASETS_DIR.joinpath(*rel_parts)
                if candidate.exists():
                    return Image.open(candidate)
        return Image.open(path)

    def preprocess(self, image_input: Union[str, Path, Image.Image]) -> torch.Tensor:
        """Transform an input radiograph into a normalized [1, H, W] PyTorch tensor."""
        img = self.load_image(image_input)
        gray = img.convert("L")
        letterboxed = self.letterbox_image(gray)

        # Scale to [0.0, 1.0] float32
        arr = np.array(letterboxed, dtype=np.float32) / 255.0

        # Channel normalization: (x - mean) / std
        normalized = (arr - self.mean) / self.std

        # Shape [H, W] -> [1, H, W]
        tensor = torch.from_numpy(normalized).unsqueeze(0)
        return tensor

    def __call__(self, image_input: Union[str, Path, Image.Image]) -> torch.Tensor:
        return self.preprocess(image_input)
