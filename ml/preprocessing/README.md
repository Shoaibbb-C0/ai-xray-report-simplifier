# Preprocessing Pipeline

## Purpose
Standardizes arbitrary medical radiographs into consistent PyTorch tensors for model consumption.

## Core Operations
1. **Aspect Ratio Preservation**: Resizing radiographs with letterboxing/padding rather than anisotropic stretching.
2. **Channel Standardization**: Conversion to single-channel (grayscale) or normalized 3-channel tensors.
3. **Intensity Normalization**: Floating-point scaling to `[0.0, 1.0]` followed by channel standardization.
4. **Data Augmentation**: Robust training transforms (subtle rotations, slight affine scaling, brightness jittering) avoiding anatomical distortion.
