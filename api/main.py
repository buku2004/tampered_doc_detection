"""
main.py
-------
FastAPI server — 4 endpoints:

  GET  /health    → model loaded? db ready?
  POST /verify    → upload document image → get verdict
  GET  /history   → last N verifications from SQLite
  GET  /stats     → summary statistics

Run with:
  cd Doc_intel
  uvicorn api.main:app --reload --port 8000

API docs at: http://localhost:8000/docs
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    VerificationResponse,
    HistoryResponse,
    StatsResponse,
    HealthResponse,
)
from pipeline.verifier import verify_document, _clf
from database.db import init_db, save_verification, get_history, get_stats
from app.config import VALID_EXTENSIONS, MAX_FILE_SIZE_MB

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Document Intelligence System",
    description = "Document authenticity verification using ELA + Random Forest",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    print("Server ready.")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    """Check if model and database are ready."""
    return HealthResponse(
        status       = "ok",
        model_loaded = _clf is not None,
        db_ready     = True,
    )


@app.post("/verify", response_model=VerificationResponse)
async def verify(file: UploadFile = File(...)):
    """
    Upload a document image (JPG/PNG) and get an authenticity verdict.

    Returns label (authentic/tampered), confidence score,
    ELA statistics, and extracted OCR text.
    """
    # ── Validate file type ────────────────────────────────────────────────────
    suffix = "." + file.filename.split(".")[-1].lower()
    if suffix not in VALID_EXTENSIONS:
        raise HTTPException(
            status_code = 400,
            detail      = f"Unsupported file type '{suffix}'. "
                           f"Allowed: {sorted(VALID_EXTENSIONS)}",
        )

    # ── Validate file size ────────────────────────────────────────────────────
    file_bytes = await file.read()
    size_mb    = len(file_bytes) / 1024 / 1024
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code = 413,
            detail      = f"File too large ({size_mb:.1f} MB). "
                           f"Max allowed: {MAX_FILE_SIZE_MB} MB",
        )

    # ── Run pipeline ──────────────────────────────────────────────────────────
    try:
        result = verify_document(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    # ── Save to database ──────────────────────────────────────────────────────
    save_verification(result, filename=file.filename)

    # ── Build human-readable verdict ──────────────────────────────────────────
    if result.is_uncertain:
        verdict = f"Uncertain — confidence too low ({result.confidence:.0%}). Manual review recommended."
    elif result.label == "tampered":
        verdict = f"TAMPERED — {result.confidence:.0%} confidence. Possible digital manipulation detected."
    else:
        verdict = f"Authentic — {result.confidence:.0%} confidence. No tampering detected."

    return VerificationResponse(
        request_id         = result.request_id,
        filename           = file.filename,
        label              = result.label,
        confidence         = result.confidence,
        authentic_prob     = result.authentic_prob,
        tampered_prob      = result.tampered_prob,
        is_uncertain       = result.is_uncertain,
        ela_mean           = result.ela_mean,
        ela_region_std     = result.ela_region_std,
        ocr_text           = result.ocr_text,
        ocr_confidence     = result.ocr_confidence,
        processing_time_ms = result.processing_time_ms,
        verdict            = verdict,
    )


@app.get("/history", response_model=HistoryResponse)
def history(limit: int = Query(default=20, ge=1, le=100)):
    """Return the last N verification requests from the database."""
    results = get_history(limit)
    return HistoryResponse(total=len(results), results=results)


@app.get("/stats", response_model=StatsResponse)
def stats():
    """Return summary statistics across all verifications."""
    data = get_stats()
    return StatsResponse(**data) if data else StatsResponse()