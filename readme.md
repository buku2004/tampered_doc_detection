# Document Intelligence System

A production-grade **document authenticity verification system** that detects digitally tampered documents (passports, degree certificates, employment letters, licenses) using **Error Level Analysis (ELA)** combined with a **Random Forest classifier**.

Built as part of an AI portfolio targeting document verification and digital forensics roles.

---

## What it does

Upload a scanned document image → the system returns:
- **Label** — `authentic` or `tampered`
- **Confidence score** — 0.0 to 1.0
- **ELA map** — visual anomaly map showing suspicious regions
- **OCR text** — extracted text from the document
- **Audit log** — every request stored in SQLite

---

## How it works

```
Input Image (JPG/PNG)
       │
       ▼
Preprocessor (OpenCV)
Deskew → Denoise → Normalize
       │
       ├──────────────────────┐
       ▼                      ▼
ELA Analyzer            OCR Engine
Re-save JPEG            Tesseract 5
Pixel diff map          Text + confidence
       │                      │
       └──────────┬───────────┘
                  ▼
        Feature Extractor
        18 numerical features
                  │
                  ▼
        Random Forest Classifier
        200 trees → authentic / tampered
                  │
                  ▼
        FastAPI Response + SQLite log
```

### What is ELA?

Error Level Analysis is a forensic technique that detects JPEG re-compression artifacts. When a document is digitally tampered (text changed, photo swapped), the edited region was saved at a different compression level — ELA reveals this as a bright patch in the anomaly map.

### Feature Vector (18 features)

| Feature | Description |
|---------|-------------|
| `ela_mean` | Average ELA map brightness |
| `ela_std` | ELA value spread |
| `ela_max` | Brightest pixel |
| `ela_p90/p95` | 90th/95th percentile brightness |
| `ela_bright_pct` | % pixels above threshold 20 |
| `ela_high_pct` | % pixels above threshold 50 |
| `ela_region_std` | Std of 32×32 block means — **key feature** |
| `noise_var` | High-frequency noise variance |
| `edge_density` | Canny edge pixel fraction |
| `texture_contrast` | Local contrast measure |
| `texture_energy` | Texture homogeneity |
| `color_std_r/g` | RGB channel std |
| `aspect_ratio` | Image width/height ratio |
| `brightness_mean/std` | Overall brightness stats |
| `ocr_confidence` | Tesseract confidence score |

---

## Model Performance

Trained on **CASIA v2** dataset (12,614 images — 7,491 authentic + 5,123 tampered):

| Metric | Authentic | Tampered |
|--------|-----------|----------|
| Precision | 0.82 | 0.75 |
| Recall | 0.83 | 0.74 |
| F1 Score | 0.83 | 0.74 |
| **Accuracy** | **79.39%** | |

Confusion Matrix:
```
                  Predicted authentic  Predicted tampered
Actual authentic         1245                253
Actual tampered           267                758
```

---

## Project Structure

```
Doc_intel/
├── Dockerfile                  # FastAPI container
├── Dockerfile.streamlit        # Streamlit container
├── docker-compose.yml          # Run both together
├── deploy_gcp.sh               # One-click GCP deployment
├── requirements.txt
│
├── app/
│   ├── config.py               # All settings in one place
│   └── models/
│       └── classifier.pkl      # Trained Random Forest (39 MB)
│
├── pipeline/
│   ├── ela_analyzer.py         # Error Level Analysis
│   ├── feature_extractor.py    # 18-feature vector builder
│   ├── preprocessor.py         # OpenCV image cleaning
│   └── verifier.py             # Pipeline orchestrator
│
├── database/
│   ├── schema.sql              # SQLite table definitions
│   └── db.py                   # Save/query verifications
│
├── api/
│   ├── schemas.py              # Pydantic request/response models
│   └── main.py                 # FastAPI server
│
└── streamlit_app/
    └── app.py                  # Interactive demo UI
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- Tesseract OCR
- Docker (optional)

### Install

```bash
# Install system dependency
sudo apt install tesseract-ocr    # Ubuntu
# brew install tesseract          # macOS

# Install Python packages
pip install -r requirements.txt
```

On Windows, install the native Tesseract OCR engine separately; `pytesseract`
only provides the Python wrapper:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Restart the terminal after installation. The application automatically checks
`PATH` and the standard `Program Files` locations. For a custom installation,
set the executable explicitly:

```powershell
$env:TESSERACT_CMD = "C:\Path\To\Tesseract-OCR\tesseract.exe"
```

The Python wrapper is small. The native Windows installation typically uses
roughly 200–250 MB, so it does not significantly increase this project's
storage requirements. Tesseract is only needed for extracted text; document
verification still runs with the existing fallback when it is unavailable.

### Run locally

```bash
# Terminal 1 — start API
uvicorn api.main:app --reload --port 8000

# Terminal 2 — start UI
streamlit run streamlit_app/app.py

# Open browser
# API docs : http://localhost:8000/docs
# Streamlit: http://localhost:8501
```

### Run with Docker

```bash
# Build and start both services
docker-compose up --build

# API  → http://localhost:8000/docs
# UI   → http://localhost:8501
```

---

## API Reference

### `POST /verify`
Upload a document image for verification.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "request_id": "986857f5",
  "filename": "passport.jpg",
  "label": "authentic",
  "confidence": 0.923,
  "authentic_prob": 0.923,
  "tampered_prob": 0.077,
  "is_uncertain": false,
  "ela_mean": 15.75,
  "ela_region_std": 3.35,
  "ocr_text": "John Smith | DOB: 12/04/1990",
  "ocr_confidence": 0.82,
  "processing_time_ms": 103,
  "verdict": "Authentic — 92% confidence. No tampering detected."
}
```

### `GET /health`
Returns model and database status.

### `GET /history?limit=20`
Returns last N verifications from SQLite.

### `GET /stats`
Returns summary statistics across all verifications.

---

## Deployment

### GCP Cloud Run (production)

```bash
# Edit PROJECT_ID in deploy_gcp.sh first
chmod +x deploy_gcp.sh
./deploy_gcp.sh
```

The script:
1. Enables Cloud Run + Artifact Registry APIs
2. Builds Docker image on GCP Cloud Build
3. Deploys to Cloud Run (asia-south1 region)
4. Prints the live URL

## Skills Demonstrated

| JD Requirement | Implementation |
|---------------|----------------|
| Computer Vision + Image Processing | OpenCV preprocessing, ELA forensic analysis |
| Classical ML — Classification | sklearn Random Forest on handcrafted features |
| Feature engineering | 18 features from ELA map + OCR + texture |
| Model evaluation | Precision, recall, F1, confusion matrix |
| SQL and database | SQLite audit log with structured schema |
| Python + scikit-learn + NumPy | Core implementation |
| REST API deployment | FastAPI with 4 endpoints |
| Docker containerization | Dockerfile + docker-compose |
| Cloud deployment | GCP Cloud Run — live public API |
| Clean documented code | Docstrings, type hints, modular structure |

---

## Training

Model trained on Kaggle using CASIA v2 dataset.
See `kaggle_training.ipynb` for the full training notebook.

To retrain locally:
```bash
# Place CASIA v2 images in:
# data/training_set/authentic/   ← Au/ images
# data/training_set/tampered/    ← Tp/ images

python -m app.training.train
```

---

## License

MIT License