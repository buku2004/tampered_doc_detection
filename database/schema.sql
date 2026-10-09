-- schema.sql
-- Run once to create the database tables.
-- db.py calls this automatically on first startup.

CREATE TABLE IF NOT EXISTS verifications (
    id                  TEXT PRIMARY KEY,
    filename            TEXT NOT NULL,
    label               TEXT NOT NULL,        -- 'authentic' or 'tampered'
    confidence          REAL NOT NULL,        -- 0.0 to 1.0
    authentic_prob      REAL,
    tampered_prob       REAL,
    is_uncertain        INTEGER DEFAULT 0,    -- 0=certain, 1=uncertain
    ela_mean            REAL,
    ela_region_std      REAL,
    ocr_text            TEXT,
    ocr_confidence      REAL,
    processing_time_ms  INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_info (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    accuracy    REAL,
    n_trees     INTEGER,
    n_features  INTEGER,
    loaded_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);