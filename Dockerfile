# ==============================================================================
# SIH26096: Digital Heritage Archive & Knowledge Platform
# Production Container for Northflank Cloud & Institutional Deployment
# ==============================================================================

FROM python:3.11-slim as base

# Prevent Python from writing .pyc files and enable unbuffered terminal logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app/src

# Set working directory
WORKDIR /app

# Install system dependencies:
# - tesseract-ocr and official language packs (eng, hin, mar)
# - libgl1 and libglib2.0-0 for OpenCV headless & PyMuPDF rasterization
# - curl for Northflank and Docker container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy and install python dependencies deterministically
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-create all required persistent and cache directories with appuser ownership
RUN mkdir -p \
    /app/data/raw \
    /app/data/processed/pages \
    /app/data/processed/preprocessed \
    /app/data/manifests \
    /app/data/ground_truth \
    /app/outputs/ocr \
    /app/outputs/metrics \
    /app/outputs/reports \
    /app/results \
    /app/cache/models \
    && chown -R appuser:appgroup /app

# Copy application source code, configurations, scripts, and initial sample manifests
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup scripts/ /app/scripts/
COPY --chown=appuser:appgroup configs/ /app/configs/
COPY --chown=appuser:appgroup data/ /app/data/
COPY --chown=appuser:appgroup outputs/ /app/outputs/
COPY --chown=appuser:appgroup results/ /app/results/

# Switch to non-root user
USER appuser:appgroup

# Runtime environment defaults (configurable on Northflank)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    APP_ENV=production \
    APP_DEBUG=false \
    ARCHIVE_DATA_DIR=/app/data \
    RESULTS_DIR=/app/results \
    OUTPUTS_DIR=/app/outputs \
    MODEL_CACHE_DIR=/app/cache/models \
    EXECUTION_MODE=DEMO

# Expose HTTP port (Northflank dynamically injects PORT)
EXPOSE 8000

# Container liveness check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/health || exit 1

# Launch application server with dynamic PORT expansion
CMD ["sh", "-c", "uvicorn sih_archive.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
