"""
schemas.py
----------
Pydantic models for FastAPI request validation and response formatting.
"""

from pydantic import BaseModel
from typing import Optional


class VerificationResponse(BaseModel):
    request_id          : str
    filename            : str
    label               : str           # "authentic" or "tampered"
    confidence          : float
    authentic_prob      : float
    tampered_prob       : float
    is_uncertain        : bool
    ela_mean            : float
    ela_region_std      : float
    ocr_text            : str
    ocr_confidence      : float
    processing_time_ms  : int
    verdict             : str           # human-readable summary


class HistoryResponse(BaseModel):
    total   : int
    results : list[dict]


class StatsResponse(BaseModel):
    total               : Optional[int]   = 0
    total_authentic     : Optional[int]   = 0
    total_tampered      : Optional[int]   = 0
    total_uncertain     : Optional[int]   = 0
    avg_confidence      : Optional[float] = 0.0
    avg_processing_ms   : Optional[float] = 0.0
    model_accuracy      : float           = 0.7939


class HealthResponse(BaseModel):
    status      : str
    model_loaded: bool
    db_ready    : bool