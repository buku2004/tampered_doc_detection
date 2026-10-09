"""
feature_extractor.py
--------------------
18 features — MUST be identical to Kaggle training notebook.
Any change here breaks the trained model.
"""

import numpy as np
from PIL import Image, ImageFilter
from app.config import IMAGE_RESIZE, BRIGHT_THRESHOLD, HIGH_THRESHOLD, BLOCK_SIZE

FEATURE_NAMES = [
    "ela_mean", "ela_std", "ela_max",
    "ela_p90", "ela_p95",
    "ela_bright_pct", "ela_high_pct", "ela_region_std",
    "noise_var", "edge_density",
    "texture_contrast", "texture_energy",
    "color_std_r", "color_std_g",
    "aspect_ratio", "brightness_mean", "brightness_std",
    "ocr_confidence",
]


def extract_features(
    ela_gray: np.ndarray,
    original_pil: Image.Image,
    ocr_confidence: float = 0.5,
) -> np.ndarray:
    """
    Returns np.ndarray shape (18,) float32.
    ocr_confidence: 0.0–1.0, pass 0.5 if OCR was skipped.
    """
    features = []
    ela_flat = ela_gray.flatten()

    # ELA statistics (0–7)
    features.append(float(np.mean(ela_flat)))
    features.append(float(np.std(ela_flat)))
    features.append(float(np.max(ela_flat)))
    features.append(float(np.percentile(ela_flat, 90)))
    features.append(float(np.percentile(ela_flat, 95)))
    features.append(float(np.mean(ela_flat > BRIGHT_THRESHOLD)))
    features.append(float(np.mean(ela_flat > HIGH_THRESHOLD)))

    H, W = ela_gray.shape
    block_means = []
    for y in range(0, H - BLOCK_SIZE + 1, BLOCK_SIZE):
        for x in range(0, W - BLOCK_SIZE + 1, BLOCK_SIZE):
            block_means.append(np.mean(ela_gray[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE]))
    features.append(float(np.std(block_means)) if block_means else 0.0)

    # Texture / noise (8–13)
    gray_np = np.array(
        original_pil.convert("L").resize(IMAGE_RESIZE), dtype=np.float32
    )
    blurred = np.array(
        original_pil.convert("L").resize(IMAGE_RESIZE).filter(ImageFilter.GaussianBlur(2)),
        dtype=np.float32,
    )
    noise = gray_np - blurred
    features.append(float(np.var(noise)))

    gy = np.abs(np.diff(gray_np, axis=0, prepend=gray_np[:1]))
    gx = np.abs(np.diff(gray_np, axis=1, prepend=gray_np[:, :1]))
    grad_mag = np.sqrt(gx**2 + gy**2)
    edge_thresh = np.mean(grad_mag) + np.std(grad_mag)
    features.append(float(np.mean(grad_mag > edge_thresh)))

    local_mean = np.array(
        original_pil.convert("L").resize(IMAGE_RESIZE).filter(ImageFilter.BoxBlur(3)),
        dtype=np.float32,
    )
    features.append(float(np.std(gray_np - local_mean)))
    features.append(float(np.mean((gray_np / 255.0) ** 2)))

    rgb_np = np.array(
        original_pil.convert("RGB").resize(IMAGE_RESIZE), dtype=np.float32
    )
    features.append(float(np.std(rgb_np[:, :, 0])))
    features.append(float(np.std(rgb_np[:, :, 1])))

    # Image-level (14–17)
    w, h = original_pil.size
    features.append(float(w / h) if h > 0 else 1.0)
    features.append(float(np.mean(gray_np)))
    features.append(float(np.std(gray_np)))
    features.append(float(np.clip(ocr_confidence, 0.0, 1.0)))

    return np.array(features, dtype=np.float32)