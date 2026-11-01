"""
config.py
---------
Single source of truth for all paths and settings.
"""

import os
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent   # Doc_intel/

# ── Model ─────────────────────────────────────────────────────────────────────
CLASSIFIER_PATH   = ROOT_DIR / "app" / "models" / "classifier.pkl"

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH           = ROOT_DIR / "database" / "doc_intel.db"

# ── ELA settings — MUST match Kaggle training notebook ───────────────────────
ELA_QUALITY       = 90
ELA_AMPLIFY       = 15
IMAGE_RESIZE      = (512, 512)

# ── Feature extraction thresholds — MUST match Kaggle ────────────────────────
BRIGHT_THRESHOLD  = 20
HIGH_THRESHOLD    = 50
BLOCK_SIZE        = 32

# ── Classifier labels ─────────────────────────────────────────────────────────
LABEL_AUTHENTIC   = 0
LABEL_TAMPERED    = 1
LABEL_NAMES       = {0: "authentic", 1: "tampered"}

# ── Confidence threshold — below this = uncertain ────────────────────────────
CONFIDENCE_THRESHOLD = 0.65

# ── Supported upload formats ──────────────────────────────────────────────────
VALID_EXTENSIONS  = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
MAX_FILE_SIZE_MB  = 10

# ── Tesseract OCR ───────────────────────────────────────────────────────────
# Set TESSERACT_CMD when Tesseract is installed outside the standard locations.
TESSERACT_CMD = os.getenv("TESSERACT_CMD")