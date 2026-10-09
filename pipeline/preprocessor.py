"""
preprocessor.py
---------------
Cleans a raw uploaded document image before ELA + OCR.
Steps:
  1. Convert to RGB (handle RGBA, grayscale, palette uploads)
  2. Resize if too large (keeps aspect ratio, caps at 2048px)
  3. Denoise (light Gaussian blur to remove scan noise)
  4. Normalize brightness (stretch contrast if image is too dark/washed out)

Returns a clean PIL Image ready for ela_analyzer and ocr_engine.
"""

import numpy as np
from PIL import Image, ImageFilter, ImageOps


# Maximum dimension before we resize down
MAX_DIMENSION = 2048


def preprocess(pil_image: Image.Image) -> Image.Image:
    """
    Clean a raw uploaded image.

    Parameters
    ----------
    pil_image : PIL.Image  (any mode, any size)

    Returns
    -------
    PIL.Image  RGB mode, max 2048px on longest side
    """
    # ── Step 1: normalize mode to RGB ────────────────────────────────────────
    if pil_image.mode == "RGBA":
        # paste onto white background — removes transparency
        background = Image.new("RGB", pil_image.size, (255, 255, 255))
        background.paste(pil_image, mask=pil_image.split()[3])
        image = background
    elif pil_image.mode != "RGB":
        image = pil_image.convert("RGB")
    else:
        image = pil_image.copy()

    # ── Step 2: resize if too large ───────────────────────────────────────────
    w, h = image.size
    if max(w, h) > MAX_DIMENSION:
        scale  = MAX_DIMENSION / max(w, h)
        new_w  = int(w * scale)
        new_h  = int(h * scale)
        image  = image.resize((new_w, new_h), Image.LANCZOS)

    # ── Step 3: light denoise ─────────────────────────────────────────────────
    # Very slight blur removes JPEG scan artifacts without destroying edges
    # radius=0.5 is subtle — just enough to reduce high-freq noise
    image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

    # ── Step 4: normalize brightness ─────────────────────────────────────────
    # If image is very dark or very washed out, autocontrast fixes it
    # This helps ELA work consistently regardless of scanner settings
    image = ImageOps.autocontrast(image, cutoff=1)

    return image


def preprocess_from_bytes(file_bytes: bytes) -> Image.Image:
    """
    Load from raw bytes (used by FastAPI file upload handler).

    Parameters
    ----------
    file_bytes : bytes  — raw content of uploaded file

    Returns
    -------
    PIL.Image  RGB, preprocessed
    """
    import io
    pil_image = Image.open(io.BytesIO(file_bytes))
    return preprocess(pil_image)