# SIH26096 — Northflank Cloud & Docker Deployment Guide

**System:** Digital Heritage Archive for Memorials, Manuscripts & Ambedkar: AI-Powered Institutional Archive and Audio-Visual Knowledge Platform  
**Target Environment:** Northflank Cloud (Container Service / Persistent Volume) + On-Premises Archival Kiosks  
**Base Image:** `python:3.11-slim` with system Tesseract OCR v5 (`eng`, `hin`, `mar`)  
**Security Profile:** Non-root execution (`appuser:appgroup`, UID 10001), path traversal defense, upload size limits  
**Research Integrity Level:** Strict separation between `DEMO / SYNTHETIC DATA` and `VALIDATED EMPIRICAL HISTORICAL RESULTS`  

---

## 1. System Architecture

The deployed Northflank container acts as the software, AI, and institutional archive services layer for the SIH26096 physical architecture. It coordinates with physical edge components (digitization workstations, archival storage servers, and memorial kiosks) through REST APIs and persistent volume sync.

```
                    +------------------------------------------------+
                    |          Institutional User / Kiosk            |
                    +-----------------------+------------------------+
                                            | HTTPS
                                            v
                    +------------------------------------------------+
                    |        Northflank Ingress / Reverse Proxy      |
                    |              (SSL Termination, Port)           |
                    +-----------------------+------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------+
|                        Docker Container (appuser:10001)                           |
|                                                                                   |
|   +-----------------------+   +------------------------+   +------------------+   |
|   |  FastAPI Web Service  |   | Resilient Search Engine|   | Attribution & QA |   |
|   |  - /health & /ready   |   | - BM25 Lexical         |   | - Citation Span  |   |
|   |  - /api/v1/diagnostics|   | - 3-Gram Fuzzy         |   | - Bounding Boxes |   |
|   |  - /api/v1/ingest     |   | - Dense Mock / BGE-M3  |   | - Refusal Gate   |   |
|   |  - Interactive Web UI |   | - Hybrid RRF (k=60)    |   |                  |   |
|   +-----------+-----------+   +-----------+------------+   +--------+---------+   |
|               |                           |                         |             |
|               +---------------------------+-------------------------+             |
|                                           |                                       |
|                                           v                                       |
|                       +---------------------------------------+                   |
|                       |   Tesseract OCR Adapter (v5 CLI)     |                   |
|                       |   - eng, hin, mar language models     |                   |
|                       +---------------------------------------+                   |
+-------------------------------------------+---------------------------------------+
                                            |
                                            v (Configurable Storage Paths)
                    +------------------------------------------------+
                    |       Mounted Persistent Volume (Northflank)   |
                    |  - /data/raw (Archival PDFs & Scans)           |
                    |  - /data/manifests (Rights & Provenance JSON)  |
                    |  - /data/ground_truth (Verified Transcripts)   |
                    |  - /results (Machine-readable JSON benchmarks) |
                    |  - /cache/models (Model Weights & Embeddings)  |
                    +------------------------------------------------+
```

---

## 2. Local Docker Run

To build and run the container locally on any workstation with Docker installed:

### Build Image
```bash
docker build -t sih26096-archive:latest .
```

### Run Container with Local Volume Mount
```bash
docker run -d \
  --name sih-archive \
  -p 8000:8000 \
  -e PORT=8000 \
  -e APP_ENV=production \
  -e EXECUTION_MODE=DEMO \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  sih26096-archive:latest
```

### Verify Container Logs
```bash
docker logs -f sih-archive
```

### Test Liveness & Readiness Locally
```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

---

## 3. Northflank Setup Guide

### Step 1: Create Project & Link Repository
1. Log into your [Northflank Dashboard](https://app.northflank.com).
2. Create a new Project (e.g. `sih-2026-digital-heritage`).
3. Under **Integrations**, connect your GitHub account and select repository `GeekLuffy/SIH26096`.

### Step 2: Create a Deployment Service
1. Navigate to **Services** -> **Create New Service** -> **Deployment Service**.
2. Select **Build from Git repository**.
3. Branch: `main`.
4. Build Type: **Dockerfile** (Northflank automatically detects the root `Dockerfile`).
5. Context Directory: `/`.

### Step 3: Configure Networking & Ports
1. Under **Networking**, add a Port:
   - Port number: `8000` (or leave default).
   - Protocol: `HTTP`.
   - Public Exposure: Enable public access (creates secure `*.northflank.app` domain with automatic TLS/SSL).

### Step 4: Attach Persistent Volume
To ensure archival manuscripts, scans, and manifests persist across container redeployments:
1. Navigate to **Volumes** in your Northflank project.
2. Create a persistent volume named `archive-storage` (e.g. 10GB–50GB SSD).
3. In your Deployment Service settings, mount the volume to `/app/data`.
4. Optionally mount an additional volume for model cache at `/app/cache/models`.

---

## 4. Environment Variables Reference

All application paths and behaviors are controlled by environment variables. Configure these in the **Environment** tab on Northflank:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | Injected dynamically by Northflank; application binds server here. |
| `HOST` | `0.0.0.0` | IP binding interface. Must remain `0.0.0.0` in containers. |
| `APP_ENV` | `production` | Runtime mode (`production` disables debug reload). |
| `APP_DEBUG` | `false` | Explicit debug flag; never set to `true` in production. |
| `EXECUTION_MODE` | `DEMO` | Operational mode: `DEMO` or `RESEARCH_VALIDATION`. |
| `ARCHIVE_DATA_DIR` | `/app/data` | Root directory for archival assets, raw files, and manifests. |
| `GROUND_TRUTH_DIR` | `/app/data/ground_truth` | Directory for verified paleographic reference transcripts. |
| `MANIFESTS_DIR` | `/app/data/manifests` | Directory for document provenance manifests. |
| `RAW_DIR` | `/app/data/raw` | Storage directory for raw incoming PDFs and scan images. |
| `PROCESSED_DIR` | `/app/data/processed` | Rasterized 300 DPI page images and preprocessed filters. |
| `RESULTS_DIR` | `/app/results` | Machine-readable benchmark outputs (`e1`, `e2`, `e3` JSON). |
| `OUTPUTS_DIR` | `/app/outputs` | Intermediate OCR outputs, CSV summaries, and reports. |
| `MODEL_CACHE_DIR` | `/app/cache/models` | Cache location for deep learning weights (e.g. BGE-M3). |
| `DATABASE_URL` | `None` | Optional SQL database connection string (e.g. Postgres). |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated for restricted domains). |
| `MAX_UPLOAD_SIZE_BYTES` | `52428800` (50MB) | Maximum file size permitted on `/api/v1/ingest`. |
| `OCR_DEVICE` | `cpu` | Compute device for inference: `cpu` or `cuda`. |

---

## 5. Port Configuration

Northflank dynamically allocates and manages container ports.
- The `Dockerfile` launches Uvicorn via `sh -c "uvicorn sih_archive.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"`.
- This ensures that if Northflank injects a custom `PORT` variable (e.g. `8080`, `3000`), the application binds to the injected port without failure or port conflicts.

---

## 6. Persistent Storage Requirements & Lifecycle

To prevent archival data loss when Northflank restarts or scales containers, files are categorized by persistence requirements:

| Data Type | Directory | Persistence Level | Backup Strategy | Recommended Storage |
| :--- | :--- | :--- | :--- | :--- |
| **Archival Raw Assets** | `/app/data/raw/` | **CRITICAL (Persistent)** | Daily snapshot | Mounted Persistent Volume or S3-compatible Object Storage |
| **Rights Manifests** | `/app/data/manifests/` | **CRITICAL (Persistent)** | Versioned in Git + Volume | Persistent Volume / SQL Database |
| **Ground Truth Transcripts**| `/app/data/ground_truth/` | **CRITICAL (Persistent)** | Versioned in Git + Volume | Persistent Volume |
| **Rasterized Pages** | `/app/data/processed/pages/` | **Regenerable** | Re-rendered from raw PDFs on demand | Persistent Volume or Local Cache |
| **Benchmark Results** | `/app/results/` | **Persistent Artifacts** | Exported to repo/reports | Persistent Volume |
| **OCR Hypotheses** | `/app/outputs/ocr/` | **Regenerable** | Re-computed by OCR engine | Local scratch / volume |
| **Model Embeddings Cache** | `/app/cache/models/` | **Cache** | Redownloaded if missing | Dedicated Cache Volume |

---

## 7. Optional GPU Configuration

The application is architected for CPU deployment on default instances while retaining full compatibility with GPU acceleration:
- In `sih_archive/config.py`, setting `OCR_DEVICE=cuda` routes neural embeddings and future vision-language models to CUDA.
- In Northflank, to attach a GPU:
  1. Under **Resource Plan**, select a GPU-enabled instance tier (NVIDIA T4 or A10G).
  2. Use an NVIDIA CUDA base image variant if building custom PyTorch kernels.
  3. The API diagnostics endpoint (`/api/v1/diagnostics`) reports the active compute device (`"configured_device": "cuda"` or `"cpu"`).
  4. If CUDA is requested but unavailable, the pipeline falls back gracefully to CPU with explicit logging.

---

## 8. Health Checks & Observability

Northflank uses built-in health checks for zero-downtime rolling deploys and automatic container restarts:

### Liveness Probe (`GET /health`)
- **Path:** `/health`
- **Port:** `8000`
- **Expected Status:** `200 OK`
- **Payload:** `{"status": "healthy", "service": "sih26096-archive", "timestamp": "...", "execution_mode": "DEMO"}`

### Readiness Probe (`GET /ready`)
- **Path:** `/ready`
- **Port:** `8000`
- **Checks:** Verifies filesystem writability on persistent directories and validates that retrieval index structures are loaded in memory.
- **Status:** Returns `200 OK` when ready; `503 Service Unavailable` if directories are read-only or initialization fails.

### Operational Diagnostics (`GET /api/v1/diagnostics`)
Returns system status without leaking sensitive credentials:
```json
{
  "service": "SIH26096 Archival System",
  "python_version": "3.11.9",
  "ocr_host_engine": {
    "name": "Tesseract OCR",
    "available": true,
    "diagnostic_message": "Tesseract binary found at /usr/bin/tesseract (languages: eng, hin, mar, osd)",
    "configured_device": "cpu"
  },
  "research_gates": {
    "E0_corpus_rights": "PASS (Intake & Provenance Metadata Validation: MEASURED; Legal authorization for specific corpus: NOT ESTABLISHED BY SOFTWARE TEST)",
    "E1_ocr_benchmark": "READY",
    "E2_retrieval_benchmark": "LOCKED (Gated on empirical E1 completion)",
    "E3_attribution_benchmark": "LOCKED (Gated on empirical E1/E2 validation)"
  }
}
```

---

## 9. DEMO Mode vs. Empirical Benchmark Mode

The system enforces strict visual and programmatic separation between preview demonstrations and verified empirical science.

### DEMO Mode (`EXECUTION_MODE=DEMO`)
- **Purpose:** Presentation mode for Smart India Hackathon (SIH 2026) evaluators.
- **Behavior:** Loads verified synthetic fixtures so all interactive capabilities (rasterization, OCR bounding boxes, BM25/Dense search, evidence-grounded QA, and visual bounding box highlighting) can be experienced live.
- **Disclaimers:** Every search response, QA answer, and Web UI banner displays:
  `⚠️ DEMO / SYNTHETIC DATA — NOT VALIDATED EMPIRICAL HISTORICAL RESULTS`
- **Research Safeguards & Integrity Distinctions:**
  - **Rights/provenance metadata validation:** `MEASURED` (manifest schema conformity, local file existence, SHA-256 checksum integrity).
  - **Legal authorization for a specific corpus:** `NOT ESTABLISHED BY SOFTWARE TEST` (statutory citations like Section 52(1)(q) or Section 22 record intake metadata; legal clearances require institutional custodial authorization).
  - **Phase Gating:** Prevents evaluators from confusing synthetic mock performance with real degraded manuscript OCR accuracy. E2 and E3 remain strictly locked until empirical E1 metrics exist.

### Empirical Benchmark Mode (`EXECUTION_MODE=RESEARCH_VALIDATION`)
- **Purpose:** Scientific evaluation on authentic historical scans.
- **Behavior:** Disables mock fallbacks; requires genuine host Tesseract execution and authentic scans in `data/raw/`.
- **Gating:** E2 and E3 benchmarks remain locked until empirical E1 metrics on real scans are computed and verified against independent human ground truth.

---

## 10. Empirical Benchmark Workflow on Container

When authentic historical scans are uploaded to Northflank storage:

```bash
# 1. Ingest historical scan
python scripts/ingest.py \
  --file /app/data/raw/historical_scan_001.pdf \
  --document-id historical_scan_001 \
  --title "Original Ambedkar Manuscript Extract" \
  --source-organization "National Archives of India" \
  --rights-status public \
  --rights-evidence "Indian Copyright Act 1957 Section 22" \
  --language eng

# 2. Render high-resolution page images
python scripts/render_pdf.py \
  --input /app/data/raw/historical_scan_001.pdf \
  --dpi 300

# 3. Execute OCR on container Tesseract
python scripts/run_ocr.py \
  --input data/processed/pages/historical_scan_001_p0001.png \
  --engine tesseract \
  --language eng

# 4. Evaluate against human paleographic transcript
python scripts/evaluate_ocr.py \
  --hypothesis outputs/ocr/historical_scan_001_p0001.json \
  --ground-truth data/ground_truth/historical_scan_001_p0001.json

# 5. Compile standardized benchmark results
python scripts/run_benchmarks.py --output-dir results
```

---

## 11. Troubleshooting & FAQ

### Issue: Container health check fails with 503 on `/ready`
- **Cause:** Mounted persistent volume has restrictive Linux permissions and container user (`appuser`, UID 10001) cannot write.
- **Fix:** In your Northflank volume settings or via container shell, execute `chown -R 10001:10001 /app/data` to ensure writability.

### Issue: `TesseractAdapter` reports unavailable in `/api/v1/diagnostics`
- **Cause:** Tesseract system package or language data is missing.
- **Fix:** Ensure the base Dockerfile installs `tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-hin`, and `tesseract-ocr-mar`. In the Docker container, verify with `which tesseract` and `tesseract --list-langs`.

### Issue: Large PDF uploads return HTTP 413
- **Cause:** File exceeds default 50MB ceiling.
- **Fix:** Increase the `MAX_UPLOAD_SIZE_BYTES` environment variable in Northflank (e.g. `104857600` for 100MB).

---

## 12. Deployment Security Notes

- **Non-Root Execution:** The container runs strictly as unprivileged `appuser` (UID 10001, GID 10001).
- **Path Traversal Defense:** Both the intake CLI and REST API use strict regex constraints (`^[a-zA-Z0-9_\-]+$`) and `os.path.commonpath` checks to block traversal attacks (e.g. `../../etc/passwd`).
- **File Extension Whitelist:** Uploads are strictly restricted to `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, and `.tif`. Executables and shell scripts are rejected.
- **No Committed Secrets:** Credentials, keys, and tokens are decoupled and injected exclusively via environment variables. Diagnostics endpoints automatically redact sensitive connection strings.
- **CORS Protection:** Configurable via `CORS_ORIGINS` to allow institutional kiosk or portal domains while restricting arbitrary origins.
