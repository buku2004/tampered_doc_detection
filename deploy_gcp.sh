#!/bin/bash
# deploy_gcp.sh
# -------------
# Builds Docker image, pushes to GCP Artifact Registry,
# deploys to Cloud Run.
#
# Prerequisites:
#   1. GCP account with billing enabled
#   2. gcloud CLI installed and authenticated
#   3. Run once:  gcloud auth login
#   4. Run once:  gcloud auth configure-docker asia-south1-docker.pkg.dev
#
# Usage:
#   chmod +x deploy_gcp.sh
#   ./deploy_gcp.sh

set -e   # stop on any error

# ── EDIT THESE ────────────────────────────────────────────────────────────────
PROJECT_ID="doc-intel-amit-2026"       # e.g. "doc-intel-amit"
REGION="asia-south1"                   # Mumbai — closest to Bangalore
SERVICE_NAME="doc-intel-api"
IMAGE_NAME="doc-intel-api"
# ─────────────────────────────────────────────────────────────────────────────

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}"
IMAGE_TAG="${REGISTRY}/${IMAGE_NAME}:latest"

echo "=================================================="
echo " Document Intelligence System — GCP Deployment"
echo "=================================================="
echo " Project  : ${PROJECT_ID}"
echo " Region   : ${REGION}"
echo " Service  : ${SERVICE_NAME}"
echo " Image    : ${IMAGE_TAG}"
echo "=================================================="

# ── Step 1: Set project ───────────────────────────────────────────────────────
echo ""
echo "[1/5] Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# ── Step 2: Enable required APIs ─────────────────────────────────────────────
echo "[2/5] Enabling GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com

# ── Step 3: Create Artifact Registry repository ───────────────────────────────
echo "[3/5] Creating Artifact Registry..."
gcloud artifacts repositories create ${SERVICE_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Document Intelligence System" \
    2>/dev/null || echo "  Repository already exists, skipping."

# ── Step 4: Build and push image ──────────────────────────────────────────────
echo "[4/5] Building and pushing Docker image..."
echo "  This takes 3-5 minutes on first build..."
gcloud builds submit \
    --tag ${IMAGE_TAG} \
    --timeout=600s \
    .

# ── Step 5: Deploy to Cloud Run ───────────────────────────────────────────────
echo "[5/5] Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_TAG} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 3 \
    --port 8000 \
    --set-env-vars PYTHONUNBUFFERED=1

echo ""
echo "=================================================="
echo " Deployment complete!"
echo "=================================================="
echo ""
# Get and print the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')

echo " API live at : ${SERVICE_URL}"
echo " Health check: ${SERVICE_URL}/health"
echo " API docs    : ${SERVICE_URL}/docs"
echo ""
echo " Test with:"
echo "   curl ${SERVICE_URL}/health"
echo ""
echo " Upload a document:"
echo "   curl -X POST ${SERVICE_URL}/verify \\"
echo "     -F 'file=@/path/to/your/document.jpg'"
echo "=================================================="
