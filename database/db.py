"""
db.py
-----
SQLite database — saves every verification request for audit logging.
Provides query functions for the /history and /stats API endpoints.
"""

import sqlite3
from pathlib import Path
from app.config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    return conn


def init_db():
    """Create tables if they don't exist. Called once at server startup."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    sql = SCHEMA_PATH.read_text()
    with _get_connection() as conn:
        conn.executescript(sql)
    print(f"Database ready at {DB_PATH}")


def save_verification(result, filename: str):
    """Insert one verification result into the database."""
    sql = """
        INSERT INTO verifications (
            id, filename, label, confidence,
            authentic_prob, tampered_prob, is_uncertain,
            ela_mean, ela_region_std,
            ocr_text, ocr_confidence, processing_time_ms
        ) VALUES (
            :id, :filename, :label, :confidence,
            :authentic_prob, :tampered_prob, :is_uncertain,
            :ela_mean, :ela_region_std,
            :ocr_text, :ocr_confidence, :processing_time_ms
        )
    """
    with _get_connection() as conn:
        conn.execute(sql, {
            "id"                 : result.request_id,
            "filename"           : filename,
            "label"              : result.label,
            "confidence"         : result.confidence,
            "authentic_prob"     : result.authentic_prob,
            "tampered_prob"      : result.tampered_prob,
            "is_uncertain"       : int(result.is_uncertain),
            "ela_mean"           : result.ela_mean,
            "ela_region_std"     : result.ela_region_std,
            "ocr_text"           : result.ocr_text,
            "ocr_confidence"     : result.ocr_confidence,
            "processing_time_ms" : result.processing_time_ms,
        })


def get_history(limit: int = 20) -> list[dict]:
    """Return the last N verifications."""
    sql = """
        SELECT * FROM verifications
        ORDER BY created_at DESC
        LIMIT ?
    """
    with _get_connection() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    """Return summary statistics for the /stats endpoint."""
    sql = """
        SELECT
            COUNT(*)                                          AS total,
            SUM(CASE WHEN label='authentic' THEN 1 ELSE 0 END) AS total_authentic,
            SUM(CASE WHEN label='tampered'  THEN 1 ELSE 0 END) AS total_tampered,
            SUM(CASE WHEN is_uncertain=1    THEN 1 ELSE 0 END) AS total_uncertain,
            ROUND(AVG(confidence), 4)                         AS avg_confidence,
            ROUND(AVG(processing_time_ms), 1)                 AS avg_processing_ms
        FROM verifications
    """
    with _get_connection() as conn:
        row = conn.execute(sql).fetchone()
    return dict(row) if row else {}