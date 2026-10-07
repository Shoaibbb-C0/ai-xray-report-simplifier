# ML Module — AI X-Ray Project

## Core Principle: In-House Trained Models Only
This project strictly avoids using third-party commercial or generative AI APIs (such as OpenAI, Gemini, Claude, or Hugging Face hosted inference endpoints) for X-ray interpretation. 

All clinical visual recognition and anomaly identification models will be engineered, trained, validated, and evaluated in-house using **PyTorch** on publicly available, peer-reviewed medical datasets (e.g., NIH ChestX-ray14, CheXpert, MURA).

## Directory Organization & Responsibilities

| Directory | Responsibility | Status |
| :--- | :--- | :--- |
| `datasets/` | Manifests, dataset download scripts, metadata, and local directory definitions. Actual raw images and large tarballs are git-ignored. | Foundation ready (no data downloaded yet) |
| `preprocessing/` | Data transformation pipelines: aspect-ratio-preserving padding, normalization, resizing, grayscale conversion, and data augmentation. | Foundation ready |
| `training/` | PyTorch model definitions, loss functions, optimizer configurations, training loops, and validation checkpoints. | Foundation ready (training scheduled for future stage) |
| `evaluation/` | Performance benchmarking scripts: confusion matrices, ROC-AUC, sensitivity, specificity, and calibration curves. | Foundation ready |
| `inference/` | Clean runtime inference routines for loading trained PyTorch `.pth` weights and processing new image inputs. | Foundation ready |
| `saved_models/` | Storage location for serialized PyTorch weights (`.pth`, `.pt`). Weight binaries are strictly git-ignored. | Foundation ready (no fake models generated) |
| `learning/` | Preserved early learning experiments (e.g. `image_basics.py`, `simple_cnn.py`, sample tensors). | Preserved & active |

## Central Configuration
See [`config.py`](./config.py) for data schemas defining supported body parts, model categories, image input specifications, and confidence threshold policies.
