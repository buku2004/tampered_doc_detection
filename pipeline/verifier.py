"""
verifier.py
-----------
Orchestrates the full inference pipeline for one document image.

Flow:
  raw bytes
    → preprocessor      (clean image)
    → ela_analyzer      (compute ELA map)
    → ocr_engine        (extract text + confidence)
    → feature_extractor (18 numbers)
    → classifier        (authentic / tampered + confidence)
    → VerificationResult

This is the only file the FastAPI route needs to call.
"""

import io
import logging
import os
import pickle
import shutil
import time
import uuid
import numpy as np
from PIL import Image
from dataclasses import dataclass
from pathlib import Path

from app.config import (
    CLASSIFIER_PATH,
    LABEL_NAMES,
    CONFIDENCE_THRESHOLD,
    TESSERACT_CMD,
)
from pipeline.preprocessor      import preprocess
from pipeline.ela_analyzer       import compute_ela_from_pil
from pipeline.feature_extractor  import extract_features

logger = logging.getLogger(__name__)

# ── Load model once at import time ───────────────────────────────────────────
# This runs when the FastAPI server starts — not on every request
print(f"Loading model from {CLASSIFIER_PATH} ...")
with open(CLASSIFIER_PATH, "rb") as f:
    _bundle = pickle.load(f)

_clf = _bundle["classifier"]
print(f"Model loaded — {_clf.n_estimators} trees, "
      f"accuracy {_bundle['accuracy']*100:.1f}%")


# ── Result dataclass ──────────────────────────────────────────────────────────
@dataclass
class VerificationResult:
    request_id          : str
    label               : str          # "authentic" or "tampered"
    confidence          : float        # 0.0 – 1.0  (confidence in the label)
    authentic_prob      : float        # raw probability for authentic
    tampered_prob       : float        # raw probability for tampered
    is_uncertain        : bool         # True if confidence < threshold
    ela_mean            : float        # key ELA stat for API response
    ela_region_std      : float        # key ELA stat for API response
    ocr_text            : str          # extracted text (empty if OCR skipped)
    ocr_confidence      : float        # tesseract confidence 0–1
    processing_time_ms  : int


# ── Main function ─────────────────────────────────────────────────────────────
def verify_document(file_bytes: bytes) -> VerificationResult:
    """
    Run the full pipeline on a single uploaded document image.

    Parameters
    ----------
    file_bytes : bytes  — raw content of the uploaded file

    Returns
    -------
    VerificationResult
    """
    t_start = time.time()
    request_id = str(uuid.uuid4())[:8]

    # ── 1. Preprocess ─────────────────────────────────────────────────────────
    pil_image = Image.open(io.BytesIO(file_bytes))
    clean_image = preprocess(pil_image)

    # ── 2. ELA ────────────────────────────────────────────────────────────────
    ela_rgb, ela_gray = compute_ela_from_pil(clean_image)

    # ── 3. OCR ────────────────────────────────────────────────────────────────
    ocr_text, ocr_confidence = _run_ocr(clean_image)

    # ── 4. Feature extraction ─────────────────────────────────────────────────
    feature_vector = extract_features(
        ela_gray       = ela_gray,
        original_pil   = clean_image,
        ocr_confidence = ocr_confidence,
    )

    # ── 5. Classify ───────────────────────────────────────────────────────────
    X = feature_vector.reshape(1, -1)
    probs       = _clf.predict_proba(X)[0]   # [prob_authentic, prob_tampered]
    pred_label  = int(_clf.predict(X)[0])

    authentic_prob = float(probs[0])
    tampered_prob  = float(probs[1])
    confidence     = float(max(probs))
    label          = LABEL_NAMES[pred_label]
    is_uncertain   = confidence < CONFIDENCE_THRESHOLD

    processing_ms = int((time.time() - t_start) * 1000)

    return VerificationResult(
        request_id         = request_id,
        label              = label,
        confidence         = round(confidence, 4),
        authentic_prob     = round(authentic_prob, 4),
        tampered_prob      = round(tampered_prob, 4),
        is_uncertain       = is_uncertain,
        ela_mean           = round(float(feature_vector[0]), 4),
        ela_region_std     = round(float(feature_vector[7]), 4),
        ocr_text           = ocr_text[:500],   # cap at 500 chars for response
        ocr_confidence     = round(ocr_confidence, 4),
        processing_time_ms = processing_ms,
    )


# ── OCR helper ────────────────────────────────────────────────────────────────
def _run_ocr(pil_image: Image.Image) -> tuple[str, float]:
    """
    Run Tesseract OCR when the native engine is available.

    The Python ``pytesseract`` package is only a wrapper; this function also
    discovers the native executable on Windows. OCR remains optional so image
    verification can continue when the engine is not installed.
    """
    try:
        import pytesseract

        tesseract_cmd = _find_tesseract()
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        data = pytesseract.image_to_data(
            pil_image,
            output_type=pytesseract.Output.DICT,
        )
        # Filter out empty/low-confidence words
        confidences = [
            int(c) for c, txt in zip(data["conf"], data["text"])
            if txt.strip() and int(c) > 0
        ]
        text = " ".join(
            txt for txt in data["text"] if txt.strip()
        )
        mean_conf = float(np.mean(confidences)) / 100.0 if confidences else 0.5
        return text, mean_conf

    except ImportError:
        logger.warning(
            "The pytesseract package is unavailable; continuing without OCR."
        )
        return "", 0.5
    except pytesseract.TesseractNotFoundError:
        logger.warning(
            "Tesseract OCR is unavailable; continuing without extracted text. "
            "Install Tesseract or set TESSERACT_CMD to tesseract.exe."
        )
        return "", 0.5
    except (OSError, ValueError) as exc:
        logger.warning("Tesseract OCR failed; continuing without OCR: %s", exc)
        return "", 0.5


def _find_tesseract() -> str | None:
    """Return a usable Tesseract executable path, if one can be found."""
    if TESSERACT_CMD:
        return TESSERACT_CMD

    discovered = shutil.which("tesseract")
    if discovered:
        return discovered

    if os.name == "nt":
        for candidate in (
            Path(os.environ.get("ProgramFiles", "")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe",
        ):
            if candidate.is_file():
                return str(candidate)

    return None