"""
ela_analyzer.py
---------------
Error Level Analysis — identical logic to Kaggle training notebook.
ELA_QUALITY and ELA_AMPLIFY MUST stay 90 and 15 — changing these
breaks compatibility with the trained classifier.pkl.
"""

import io
import numpy as np
from PIL import Image
from app.config import ELA_QUALITY, ELA_AMPLIFY, IMAGE_RESIZE


def compute_ela(image_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Run ELA on an image file path.
    Returns (ela_rgb, ela_gray)
    """
    original = Image.open(image_path).convert("RGB")
    original = original.resize(IMAGE_RESIZE, Image.LANCZOS)

    buf = io.BytesIO()
    original.save(buf, format="JPEG", quality=ELA_QUALITY)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    orig_arr   = np.array(original,     dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)

    diff     = np.abs(orig_arr - recomp_arr)
    ela_rgb  = np.clip(diff * ELA_AMPLIFY, 0, 255).astype(np.uint8)
    ela_gray = np.mean(ela_rgb, axis=2).astype(np.float32)

    return ela_rgb, ela_gray


def compute_ela_from_pil(pil_image: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    """
    Run ELA on a PIL Image directly (used at inference — no file path needed).
    Returns (ela_rgb, ela_gray)
    """
    original = pil_image.convert("RGB").resize(IMAGE_RESIZE, Image.LANCZOS)

    buf = io.BytesIO()
    original.save(buf, format="JPEG", quality=ELA_QUALITY)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    orig_arr   = np.array(original,     dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)

    diff     = np.abs(orig_arr - recomp_arr)
    ela_rgb  = np.clip(diff * ELA_AMPLIFY, 0, 255).astype(np.uint8)
    ela_gray = np.mean(ela_rgb, axis=2).astype(np.float32)

    return ela_rgb, ela_gray