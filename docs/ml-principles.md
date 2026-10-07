# Machine Learning Principles

## 1. Exclusively In-House Trained Models
A primary pillar of this project is the **strict prohibition** of third-party or proprietary inference APIs for medical imaging interpretation:
- **No OpenAI, Anthropic Claude, or Google Gemini** APIs are used for diagnostic inference or image classification.
- **No Hugging Face hosted inference endpoints** or generic generative vision models are relied upon.
- Every neural network performing image quality check, anatomical classification, or finding detection must be built, trained, and evaluated natively using **PyTorch**.

## 2. Public Medical Dataset Training
All training is conducted on verified, open-access, peer-reviewed clinical research datasets:
- **Chest Radiography**: e.g., NIH ChestX-ray14, Stanford CheXpert, or PadChest.
- **Musculoskeletal Radiographs**: e.g., Stanford MURA.
- Each dataset is managed locally, with scripts maintaining reproducible training/validation/test splits.

## 3. Strict Determinism and Safety
- Medical images are preprocessed with aspect-ratio-preserving padding to prevent anatomical distortion.
- Calibration analysis is mandatory before any model is deployed to inference.
- Thresholds are conservative: ambiguous signals are surfaced as inconclusive rather than presenting high-confidence speculative findings.
