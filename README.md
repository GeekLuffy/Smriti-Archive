# Smriti Archive (स्मृति आर्काइव)

### Digital Heritage Archive for Memorials, Manuscripts & Dr. B. R. Ambedkar
**Smart India Hackathon (SIH) 2026 · Problem Statement SIH26096 · Team ORBIT**

[![Production Deployment](https://img.shields.io/badge/Vercel-Live%20Production-success?logo=vercel&logoColor=white)](https://orbit-heritage-archive.vercel.app)
[![Touch Kiosk Mode](https://img.shields.io/badge/Kiosk%20Mode-Active-059669?logo=googlechrome&logoColor=white)](https://orbit-heritage-archive.vercel.app/kiosk)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-293%20Passing-brightgreen?logo=pytest&logoColor=white)](tests/)
[![Build Dependencies](https://img.shields.io/badge/Node.js%20%2F%20npm-Zero%20Dependencies-blueviolet)](#architecture)
[![Research Integrity](https://img.shields.io/badge/Research%20Integrity-Zero%20Fabrication-b91c1c)](docs/RESEARCH_INTEGRITY.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Live Production Portal:** [https://orbit-heritage-archive.vercel.app](https://orbit-heritage-archive.vercel.app)  
**Touchscreen Memorial Kiosk:** [https://orbit-heritage-archive.vercel.app/kiosk](https://orbit-heritage-archive.vercel.app/kiosk)

---

## Overview

**Smriti Archive** is a research-grade institutional digital heritage platform and memorial archive designed to preserve, index, and explore the life, writings, speeches, and constitutional legacy of **Dr. B. R. Ambedkar**. Developed for **SIH 2026 (Problem Statement SIH26096)** by **Team ORBIT**, the platform connects physical memorial items and archival scans with cryptographic provenance, resilient multi-strategy search, and evidence-grounded AI synthesis.

Unlike typical consumer chatbots or generic web portals, Smriti Archive enforces strict **provenance continuity**: every synthesized answer, search result, or catalog record is directly anchored to high-resolution (300 DPI) archival master page scans with token-level visual bounding-box coordinates.

### Key Highlights

- **Heritage-First Visual Architecture**: Museum-grade aesthetics using deep navy (`#0f172a`), warm parchment (`#fdfbf7`), and muted bronze (`#b45309`), with authentic historical scans, pull-quote banners, and timeline galleries.
- **Zero-Build Python Stack**: 100% Python backend and UI engine. No Node.js, Webpack, Vite, or `npm` build dependencies. Instant serverless cold starts (<30s deployment) and ultra-lightweight execution.
- **Dual-Surface Experience**: Complete desktop/mobile research portal with 7 discovery sections plus a dedicated, touch-first memorial kiosk mode (`/kiosk`) with minimum 48px touch targets and an ambient 8-second smart display presentation mode.
- **Multi-Strategy Gated Search**: Lexical BM25, character n-gram fuzzy retrieval, dense semantic embeddings, and hybrid Reciprocal Rank Fusion (RRF).
- **Evidence-Grounded QA & Refusal Gate**: Answers generated strictly from retrieved archival evidence with pixel coordinates. Out-of-corpus queries trigger a principled refusal card rather than hallucinating.
- **Verifiable 6-Stage Provenance Chain**: Tracks custody and SHA-256 hashes across: `Source Object → Digital Copy → Page Rasterization → OCR/Layout → Retrieval Index → Answer/Derivative`.
- **Absolute Research Integrity**: Strict gating (E0 Measured, E1 Blocked on host OCR binary, E2/E3 Locked preview) with zero synthetic metric fabrication.

---

## Table of Contents

- [System Architecture](#system-architecture)
  - [The 6-Stage Provenance Chain](#the-6-stage-provenance-chain)
  - [High-Level Component Topology](#high-level-component-topology)
  - [Directory Structure](#directory-structure)
- [Tech Stack](#tech-stack)
- [Research Integrity & Scientific Gating Matrix](#research-integrity--scientific-gating-matrix)
- [Prerequisites](#prerequisites)
- [Getting Started (Local Development)](#getting-started-local-development)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Create Virtual Environment](#2-create-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Run Automated Test Suite](#4-run-automated-test-suite)
  - [5. Launch Development Server](#5-launch-development-server)
- [End-to-End Command Line Interface (CLI)](#end-to-end-command-line-interface-cli)
  - [Step 1: Render Archival PDF (`scripts/render_pdf.py`)](#step-1-render-archival-pdf-scriptsrender_pdfpy)
  - [Step 2: Execute OCR & Preprocessing (`scripts/run_ocr.py`)](#step-2-execute-ocr--preprocessing-scriptsrun_ocrpy)
  - [Step 3: Evaluate OCR Error Metrics (`scripts/evaluate_ocr.py`)](#step-3-evaluate-ocr-error-metrics-scriptsevaluate_ocrpy)
  - [Step 4: Generate Publication Report (`scripts/generate_report.py`)](#step-4-generate-publication-report-scriptsgenerate_reportpy)
- [API Reference & Endpoints](#api-reference--endpoints)
  - [Core Routes](#core-routes)
  - [Sample API Interactions](#sample-api-interactions)
- [Touchscreen Kiosk & Smart Display Mode](#touchscreen-kiosk--smart-display-mode)
- [Production Deployment](#production-deployment)
  - [Vercel Serverless (Recommended)](#vercel-serverless-recommended)
  - [Docker / Container Deployment](#docker--container-deployment)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Team & Statutory Compliance](#team--statutory-compliance)
- [License](#license)

---

## System Architecture

### The 6-Stage Provenance Chain

The fundamental law of Smriti Archive is **provenance continuity**: every derivative output must trace backward through an unbroken custody chain to an authentic historical record.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Source Object  │ ───►  │  Digital Copy   │ ───►  │   Page Image    │
│ Physical Folio  │       │ Archival PDF    │       │ 300 DPI Master  │
│ Manifest & Law  │       │ SHA-256 Digest  │       │ Bounding Box    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   OCR / Layout  │ ───►  │ Retrieval Index │ ───►  │ Evidence Answer │
│ Token Hierarchy │       │ Hybrid BM25/RRF │       │ Grounded Claims │
│ Confidence BBox │       │ Candidate Rank  │       │ Refusal Gating  │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **Source Object**: Physical manuscript, debate transcript, or memorial photograph cataloged with holding institution, date, language, and legal status (Section 52(1)(q) of Indian Copyright Act 1957).
2. **Digital Copy**: Lossless archival PDF intake stored in `data/raw/` with immutable intake SHA-256 manifests.
3. **Page Image**: Deterministic 300 DPI rasterization (`{document_id}_p{page_num:04d}.png`) cached in `data/processed/pages/`.
4. **OCR / Layout**: Token-level extraction (`OCROutput`) preserving word bounding boxes `[x, y, w, h]`, line/block hierarchy, and confidence scores.
5. **Retrieval Index**: Inverted index and dense vector space supporting BM25, 3-gram fuzzy matching, and Reciprocal Rank Fusion.
6. **Evidence Answer / Derivative**: Synthesized claim supported by direct citations (`document_id`, `page_id`, and visual overlay) or disciplined refusal.

### High-Level Component Topology

```
                              HTTP Request
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │  FastAPI Application  │
                       │  (src/sih_archive/    │
                       │       api/app.py)     │
                       └───────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  HTML & Kiosk   │       │ Search Engine   │       │ QA & Evidence   │
│  Page Builders  │       │ (BM25, N-Gram,  │       │ Grounding Engine│
│  (Pure Python)  │       │  Dense, Hybrid) │       │ (Refusal Gate)  │
└─────────────────┘       └─────────────────┘       └─────────────────┘
         │                         │                         │
         ▼                         ▼                         ▼
  Browser / Kiosk          Indexed Corpus            Token BBoxes &
  (HTML5/CSS3/JS)          (data/processed/)         Citation Cards
```

### Directory Structure

```
SIH26096/
├── api/
│   └── index.py                      # Vercel serverless function entrypoint
├── configs/
│   └── e1_baseline.yaml              # Benchmark experiment configuration
├── data/
│   ├── ground_truth/                 # Human-verified reference transcripts
│   ├── manifests/                    # Document intake and legal rights manifests
│   ├── processed/
│   │   ├── pages/                    # 300 DPI rendered PNGs & historical assets
│   │   └── preprocessed/             # Intermediate image filter outputs
│   └── raw/                          # Archival PDFs and source documents
├── docs/
│   ├── DATASET_PROTOCOL.md           # Rights hygiene, scan tiers & sampling rules
│   ├── E1_OCR_RESULTS.md             # Empirical OCR benchmark status & Tesseract setup
│   ├── E2_RETRIEVAL_RESULTS.md       # Information retrieval benchmark architecture
│   ├── E3_ATTRIBUTION_RESULTS.md     # Attribution evaluator & refusal gate specs
│   ├── EXPERIMENT_PROTOCOL.md        # Reproducible benchmarking protocols
│   ├── IMPLEMENTATION_PLAN.md        # Architecture, data flows & phase contracts
│   ├── RESEARCH_INTEGRITY.md         # Truthful epistemic classification matrix
│   ├── RESULTS.md                    # Measured benchmark results
│   └── STATE_AUDIT.md                # System state audits and regression logs
├── outputs/
│   ├── metrics/                      # Evaluated CER/WER & IoU JSON/CSV metrics
│   ├── ocr/                          # Standardized OCR token outputs
│   └── reports/                      # Markdown summaries and Matplotlib figures
├── scripts/
│   ├── evaluate_ocr.py               # CLI: Standardized CER/WER evaluation engine
│   ├── generate_report.py            # CLI: Publication report & chart generator
│   ├── render_pdf.py                 # CLI: PDF to high-res image renderer
│   └── run_ocr.py                    # CLI: OCR execution engine & preprocessor
├── src/sih_archive/
│   ├── api/                          # FastAPI web routes and lifecycle handlers
│   ├── attribution/                  # Phase E3: Grounded claim synthesis & refusal gate
│   ├── evaluation/                   # Phase E1: CER/WER, IoU matching, reading order
│   ├── ingestion/                    # Phase E0: Intake validation and rights audit
│   ├── ocr/                          # Phase E1: Tesseract adapter and mock fallback
│   ├── preprocessing/                # Phase E1: OpenCV filters (CLAHE, Otsu, Deskew)
│   ├── rendering/                    # Phase E1: PyMuPDF deterministic PDF rasterization
│   ├── retrieval/                    # Phase E2: BM25, N-Gram, Dense, and Hybrid RRF
│   ├── schemas/                      # Pydantic v2 core schemas (Manifest, OCR, Token)
│   ├── ui/                           # Zero-build UI (styles, page_builder, scripts, fixtures)
│   └── utils/                        # Path security, cryptographic hashing, and helpers
├── tests/                            # Comprehensive offline test suite (293 passing)
├── Dockerfile                        # Multi-stage production container definition
├── pytest.ini                        # Pytest discovery configuration
├── requirements.txt                  # Minimal pinned runtime dependencies
├── vercel.json                       # Vercel serverless rewrite rules
└── README.md                         # Project documentation
```

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Core Language** | Python 3.11+ | Single unified runtime across research, pipeline, and web layers. |
| **Web Framework** | FastAPI 0.110+ | High-throughput asynchronous ASGI framework with automated OpenAPI docs. |
| **Frontend UI** | Zero-Build HTML5 / CSS3 / Vanilla ES6 | Generated via Python string templates; no Node.js/npm dependencies, zero hydration lag. |
| **PDF Rasterization** | PyMuPDF (fitz) 1.24+ | Fast C-accelerated 300 DPI rasterization preserving color profiles. |
| **Image Preprocessing** | OpenCV Headless + Pillow | Contrast equalization (CLAHE), Otsu thresholding, morphological denoise, deskew. |
| **OCR Engines** | Tesseract 5.x / Mock Adapter | Pluggable interface preserving word bounding boxes and confidence. |
| **Retrieval Engine** | Custom In-Memory BM25 + RapidFuzz N-Gram + BGE-M3 Dense + RRF Hybrid | Zero external database overhead; sub-5ms retrieval over archival folios. |
| **Validation** | Pydantic v2 | Strict schema validation for manifests, tokens, and benchmark metrics. |
| **Serverless Host** | Vercel Serverless Functions | Fast global edge delivery via `api/index.py`. |
| **Containerization** | Docker / Northflank | Self-contained production container with Tesseract language packs (`eng`, `hin`, `mar`). |

---

## Research Integrity & Scientific Gating Matrix

In accordance with strict academic hygiene, Smriti Archive enforces an explicit **Epistemic Classification System**. The platform refuses to present synthetic previews as empirical benchmarks.

| Phase | Description | Current Gate Status | Truthful Behavior Enforced |
|---|---|---|---|
| **E0** | Ingestion & Rights Protocol | **`MEASURED`** | SHA-256 digests verified; Indian Copyright Act 1957 Section 52(1)(q) compliance verified. |
| **E1** | Archival OCR Benchmark | **`BLOCKED_ON_HOST_OCR_BINARY`** | If Tesseract is missing on host, reports blocked state with exact installation instructions. Never synthesizes false OCR accuracy. |
| **E2** | Multi-Strategy Search Benchmark | **`LOCKED_PREVIEW`** | Search algorithms are fully operational; formal benchmark numbers remain locked until ground truth corpus is annotated. |
| **E3** | Attribution & Grounding Benchmark | **`LOCKED_PREVIEW`** | Citation pipeline works with visual bounding boxes; precision/recall metrics are locked until human ground truth is supplied. |

---

## Prerequisites

Before running Smriti Archive locally, ensure you have:

- **Python 3.11 or higher** installed (`python --version`)
- **pip** package installer
- **Git** version control
- *(Optional, for Phase E1 OCR)*: **Tesseract OCR 5.x** with `eng`, `hin`, and `mar` language data.
  - **Ubuntu / Debian**: `sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar`
  - **macOS (Homebrew)**: `brew install tesseract tesseract-lang`
  - **Windows**: Install via [UB-Mannheim Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki) and add to system `PATH`.
  - *Note: If Tesseract is not installed, the platform gracefully falls back to synthetic preview mode and passes all tests.*

---

## Getting Started (Local Development)

### 1. Clone Repository

```bash
git clone https://github.com/GeekLuffy/SIH26096.git
cd SIH26096
```

### 2. Create Virtual Environment

```bash
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Automated Test Suite

Verify that all 293 tests pass offline:

```bash
pytest tests/ -v
```

Expected output:
```
============================== 293 passed in 7.82s ==============================
```

### 5. Launch Development Server

Start the local server with auto-reload:

```bash
uvicorn sih_archive.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
- **Heritage Web Portal:** `http://localhost:8000`
- **Memorial Touch Kiosk:** `http://localhost:8000/kiosk`
- **Interactive OpenAPI Docs:** `http://localhost:8000/docs`
- **Health Check Endpoint:** `http://localhost:8000/health`

---

## End-to-End Command Line Interface (CLI)

The repository provides 4 standalone research CLI utilities in `scripts/`:

```
┌───────────────────────┐
│ Archival PDF in       │
│ data/raw/             │
└───────────┬───────────┘
            │
            ▼ 1. render_pdf.py
┌───────────────────────┐
│ 300 DPI Page Images   │
│ data/processed/pages/ │
└───────────┬───────────┘
            │
            ▼ 2. run_ocr.py
┌───────────────────────┐
│ Token JSON & BBoxes   │
│ outputs/ocr/          │
└───────────┬───────────┘
            │
            ▼ 3. evaluate_ocr.py
┌───────────────────────┐
│ CER/WER & IoU Metrics │
│ outputs/metrics/      │
└───────────┬───────────┘
            │
            ▼ 4. generate_report.py
┌───────────────────────┐
│ Publication Reports   │
│ outputs/reports/      │
└───────────────────────┘
```

### Step 1: Render Archival PDF (`scripts/render_pdf.py`)

Rasterizes raw archival PDF documents into 300 DPI master images with cryptographic provenance tracking:

```bash
python scripts/render_pdf.py \
  --input data/raw/ambedkar_speech_vol1.pdf \
  --output data/processed/pages \
  --dpi 300 \
  --pages all
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--input`, `-i` | Path | *Required* | Path to source PDF file or document manifest JSON |
| `--output`, `-o` | Path | `data/processed/pages` | Destination directory for rendered PNGs |
| `--dpi`, `-d` | Integer | `300` | Rasterization resolution in dots-per-inch |
| `--pages`, `-p` | String | `'all'` | Page selection (`'all'`, `'1'`, `'1-5'`, or `'1,3,5'`) |
| `--force`, `-f` | Flag | `False` | Force re-rendering even if output files exist |

### Step 2: Execute OCR & Preprocessing (`scripts/run_ocr.py`)

Runs optical character recognition using modular image enhancement filters:

```bash
python scripts/run_ocr.py \
  --input data/processed/pages/ambedkar_speech_vol1_p0001.png \
  --engine tesseract \
  --language eng \
  --preprocess "grayscale,clahe,denoise" \
  --output outputs/ocr \
  --force
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--input`, `-i` | Path | *Required* | Single image path or directory of page images |
| `--engine`, `-e` | String | `'tesseract'` | Adapter to invoke (`'tesseract'` or `'mock'`) |
| `--language`, `-l` | String | `'eng'` | ISO 639-3 language code (`eng`, `hin`, `mar`) |
| `--preprocess`, `-p` | String | `'raw'` | Filter sequence (`raw`, `grayscale`, `clahe`, `otsu`, `deskew`, `denoise`) |
| `--output`, `-o` | Path | `outputs/ocr` | Destination directory for OCR JSON tokens |
| `--check-only` | Flag | `False` | Verify OCR engine availability on host without processing |

### Step 3: Evaluate OCR Error Metrics (`scripts/evaluate_ocr.py`)

Computes Levenshtein Character Error Rate (CER), Word Error Rate (WER) with operation breakdown ($S, D, I$), and bounding box IoU:

```bash
python scripts/evaluate_ocr.py \
  --hypothesis outputs/ocr/ambedkar_speech_vol1_p0001.json \
  --ground-truth data/ground_truth/ambedkar_speech_vol1_p0001.json \
  --output outputs/metrics \
  --iou-threshold 0.5 \
  --normalize \
  --format both
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--hypothesis`, `-i` | Path | *Required* | OCR hypothesis JSON file or directory |
| `--ground-truth`, `-g` | Path | *Required* | Ground truth reference transcript JSON file |
| `--output`, `-o` | Path | `outputs/metrics` | Destination directory for evaluation metrics |
| `--iou-threshold` | Float | `0.5` | Bounding box intersection-over-union threshold |
| `--normalize` | Flag | `False` | Normalize contiguous whitespace and soft hyphens |
| `--format` | String | `'both'` | Report format (`'json'`, `'csv'`, `'both'`) |

### Step 4: Generate Publication Report (`scripts/generate_report.py`)

Compiles aggregated benchmark metrics into publication-ready Markdown tables and headless Matplotlib figures:

```bash
python scripts/generate_report.py \
  --metrics outputs/metrics \
  --output outputs/reports \
  --format all \
  --title "Smriti Archive Empirical OCR Benchmark Report (Phase E1)"
```

---

## API Reference & Endpoints

### Core Routes

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Renders the primary institutional heritage web portal HTML. |
| `GET` | `/kiosk` | Renders the touchscreen memorial kiosk interface (supports `?mode=ambient`). |
| `GET` | `/health` | Liveness health probe returning HTTP 200 `{"status": "healthy"}`. |
| `GET` | `/ready` | Readiness probe confirming retrieval indices and corpus are loaded. |
| `GET` | `/api/v1/diagnostics` | System diagnostic state, active gate statuses, and host OCR availability. |
| `GET` | `/api/v1/search` | Multi-strategy search (`q`, `strategy`: `bm25` \| `ngram` \| `dense` \| `hybrid`, `limit`). |
| `POST` | `/api/v1/qa` | Evidence-grounded QA returning synthesized claims, citations, and bounding boxes. |
| `GET` | `/api/v1/pages/{page_id}/image` | Serves authentic 300 DPI page scans and historical photographic assets. |
| `GET` | `/api/v1/manifests` | Lists all registered document and intellectual property manifests. |
| `POST` | `/api/v1/manifests` | Registers a verified intake manifest with cryptographic SHA-256 digest. |
| `GET` | `/api/v1/benchmarks/{phase}` | Returns formal benchmark status for `e0`, `e1`, `e2`, or `e3`. |

### Sample API Interactions

#### 1. Multi-Strategy Search (`GET /api/v1/search`)

```bash
curl -X GET "http://localhost:8000/api/v1/search?q=Constitution&strategy=hybrid&limit=3"
```

Response:
```json
{
  "query": "Constitution",
  "strategy": "hybrid",
  "total_hits": 1,
  "execution_duration_ms": 1.42,
  "results": [
    {
      "document_id": "ambedkar_speech_vol1",
      "page_id": "ambedkar_speech_vol1_p0001",
      "score": 0.032,
      "snippet": "DR. BABASAHEB AMBEDKAR WRITINGS AND SPEECHES VOL. 1... Motion Introducing Draft Constitution",
      "language": "eng",
      "provenance": {
        "holding_institution": "National Archives of India",
        "rights": "public"
      }
    }
  ]
}
```

#### 2. Evidence-Grounded QA (`POST /api/v1/qa`)

```bash
curl -X POST "http://localhost:8000/api/v1/qa" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who compiled Volume 1 of Dr. Ambedkar Writings?"}'
```

Response:
```json
{
  "question": "Who compiled Volume 1 of Dr. Ambedkar Writings?",
  "status": "grounded_answer",
  "answer": "Volume 1 was compiled by Vasant Moon and published by the Education Department, Government of Maharashtra.",
  "refusal_reason": null,
  "citations": [
    {
      "document_id": "ambedkar_speech_vol1",
      "page_id": "ambedkar_speech_vol1_p0001",
      "matched_tokens": ["Compiled", "by", "Vasant", "Moon"],
      "bounding_boxes": [[50, 180, 80, 18], [135, 180, 25, 18], [165, 180, 70, 18], [240, 180, 50, 18]]
    }
  ]
}
```

#### 3. Principled Refusal Gate (Out-of-Corpus Query)

```bash
curl -X POST "http://localhost:8000/api/v1/qa" \
  -H "Content-Type: application/json" \
  -d '{"question": "What happened on Mars in 1920?"}'
```

Response:
```json
{
  "question": "What happened on Mars in 1920?",
  "status": "refusal",
  "answer": null,
  "refusal_reason": "Insufficient archival evidence found for a supported answer.",
  "citations": []
}
```

---

## Touchscreen Kiosk & Smart Display Mode

Smriti Archive includes dedicated interfaces optimized for physical museum displays, memorial halls, and institutional kiosks:

1. **Touch Navigation (`/kiosk`)**:
   - Minimum **48px touch targets** across all buttons, inputs, and topic chips.
   - Large visual cards with archival photo banners for *Manuscripts*, *Historic Audio*, *Timeline*, and *Constitution*.
   - On-screen touch search with instant query chips (*Constituent Assembly*, *Mahad Satyagraha*, *Annihilation of Caste*, *Poona Pact*).
2. **Smart Display Mode (`/kiosk?mode=ambient`)**:
   - Ambient, self-running exhibit presentation cycling curated historical milestones every 8 seconds.
   - Animated progress bar and crossfade transitions.
   - Interactive controls: tap screen or press `Space` to pause/resume presentation; press `Esc` to return to touch kiosk.

---

## Production Deployment

### Vercel Serverless (Recommended)

Smriti Archive is engineered specifically for instantaneous zero-build deployment on Vercel:

1. **Prerequisites**: Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. **Deploy to Production**:
   ```bash
   vercel --prod
   ```
3. **Map Domain / Production Alias**:
   ```bash
   vercel alias set <deployment-url> orbit-heritage-archive.vercel.app
   ```
4. Configuration is driven automatically by `vercel.json` routing all requests through `api/index.py`.

### Docker / Container Deployment

For on-premises institutional servers or Northflank Cloud:

1. **Build Container Image**:
   ```bash
   docker build -t smriti-archive:latest .
   ```
2. **Run Container**:
   ```bash
   docker run -d \
     --name smriti-archive \
     -p 8000:8000 \
     -e APP_ENV=production \
     -e HOST=0.0.0.0 \
     -e PORT=8000 \
     smriti-archive:latest
   ```
3. **Verify Container Health**:
   ```bash
   curl http://localhost:8000/health
   ```

The included multi-stage `Dockerfile` runs as an unprivileged user (`appuser`, UID 10001) and pre-installs Tesseract OCR with `eng`, `hin`, and `mar` language models.

---

## Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `HOST` | String | `127.0.0.1` | Network interface for FastAPI/Uvicorn server |
| `PORT` | Integer | `8000` | TCP port to bind HTTP listener |
| `APP_ENV` | String | `development` | Deployment environment (`development`, `production`, `vercel`) |
| `APP_DEBUG` | Boolean | `true` | Verbose debug logging toggle |
| `ARCHIVE_DATA_DIR` | Path | `data/` | Root directory for raw and processed archival files |
| `RESULTS_DIR` | Path | `results/` | Target directory for benchmark execution output |
| `OUTPUTS_DIR` | Path | `outputs/` | Target directory for OCR token files and evaluation metrics |
| `EXECUTION_MODE` | String | `DEMO` | Platform mode (`DEMO` or `RESEARCH_BENCHMARK`) |

---

## Troubleshooting

### 1. Tesseract OCR Reports `BLOCKED_ON_HOST_OCR_BINARY`

- **Symptom:** Running `python scripts/run_ocr.py --engine tesseract` returns exit status indicating missing host binary.
- **Cause:** Tesseract executable is not installed or not present on your system `PATH`.
- **Solution:**
  - **Windows:** Install [Tesseract via UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) to `C:\Program Files\Tesseract-OCR` and add to Environment `PATH`.
  - **Linux:** `sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar`
  - **macOS:** `brew install tesseract tesseract-lang`
  - *Fallback:* You can run with `--engine mock` to test the pipeline without physical OCR binaries.

### 2. High-Resolution Archival Images Return 404

- **Symptom:** Historical photographs or page scans do not render on `/` or `/kiosk`.
- **Cause:** Processed images in `data/processed/pages/` were omitted from git tracking.
- **Solution:** Ensure `.gitignore` does not exclude `data/processed/pages/*.png`. Check that files are present:
  ```bash
  ls -lh data/processed/pages/
  ```

### 3. Vercel Custom Domain Shows Previous Deployment

- **Symptom:** `git push origin main` triggers a new Vercel build, but the vanity URL still displays older code.
- **Solution:** Explicitly assign the vanity alias using Vercel CLI:
  ```bash
  vercel alias set <new-deployment-url> orbit-heritage-archive.vercel.app
  ```

---

## Team & Statutory Compliance

### Smart India Hackathon (SIH) 2026

- **Problem Statement ID:** SIH26096 (*Digital Heritage Archive for Memorials, Manuscripts & Ambedkar*)
- **Team Name:** ORBIT
- **Core Mission:** Establishing digital heritage preservation infrastructure combining physical fidelity, cryptographic provenance, and evidence-grounded AI search.

### Statutory Intellectual Property Compliance

- **Indian Copyright Act, 1957 — Section 52(1)(q)**: The reproduction or publication of any matter published in any Official Gazette or report of any committee, commission, or council appointed by the Government is exempt from copyright infringement.
- **Section 22 (Term of Copyright in Published Literary Works)**: Works published during the author's lifetime enter the public domain 60 years following the calendar year of the author's death (1956 + 60 years = 2017).
- **Accessibility Standard**: The portal and kiosk interfaces comply with **WCAG 2.2 AA** contrast and navigation standards.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
Archival texts, parliamentary debates, and government committee reports referenced within this platform are preserved under fair dealing and public domain statutory exemptions.
