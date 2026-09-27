# SIH26096: Digital Heritage Archive & Archival OCR Benchmarking Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Research Integrity](https://img.shields.io/badge/research-zero--fabrication-red.svg)](docs/RESULTS.md)
[![Tests Passing](https://img.shields.io/badge/tests-100%25%20passing-brightgreen.svg)](tests/)

A reproducible, research-grade OCR benchmarking and provenance preservation framework (Phases E0 and E1) developed under **Smart India Hackathon (SIH) 2026 Problem Statement SIH26096** (*Digital Heritage Archive for Memorials, Manuscripts & Ambedkar*).

The system provides verifiable archival intake, high-resolution deterministic rendering, modular image preprocessing, OCR engine abstraction, edit-distance error decomposition (CER/WER), geometric bounding box IoU evaluation, and publication-ready reporting without premature production shortcuts or fabricated benchmark data.

---

## 1. System Architecture & Features

```
  Archival PDF (data/raw/)
            │
            ▼
  [scripts/render_pdf.py] ────► 300 DPI PNGs + SHA-256 Manifests (data/processed/pages/)
            │
            ▼
  [scripts/run_ocr.py] ────────► Preprocessing (CLAHE, Otsu, Deskew, Denoise)
            │                    + Common OCR Adapter (Tesseract / Mock)
            │                    └─► Structured OCR Tokens & BBoxes (outputs/ocr/)
            │
            ▼
  [scripts/evaluate_ocr.py] ───► Levenshtein CER/WER Decompositions (S, D, I)
            │                    + Greedy Bipartite IoU Bounding Box Matching
            │                    + Kendall's Tau Reading Order Consistency
            │                    └─► Evaluation Metrics JSON & CSV (outputs/metrics/)
            │
            ▼
  [scripts/generate_report.py] ─► Publication Markdown Tables & Summaries
                                 + Headless Matplotlib Visualizations (outputs/reports/)
```

- **Phase E0 (Rights & Ingestion Protocol)**: Tamper-evident intake protocol validating SHA-256 checksums, enforcing path security, and strictly cataloging rights status (`public`, `verified`, `restricted`, `unknown`) under the Indian Copyright Act 1957.
- **Phase E1 (Deterministic Rendering & Preprocessing)**: 300 DPI rasterization with deterministic `{document_id}_p{page_num:04d}` naming, duplicate rendering caching, and modular OpenCV filters (`grayscale`, `resize`, `clahe`, `otsu`, `deskew`, `denoise`).
- **Common OCR Adapter Framework**: Extensible interface preserving word bounding boxes `[x, y, w, h]`, line/block layout hierarchies, confidence scores, and truthful missing-engine diagnostics.
- **Standardized Error Metrics**: RapidFuzz-accelerated Levenshtein edit operations decomposed into substitutions ($S$), deletions ($D$), and insertions ($I$).
- **Geometric Region Matching**: Greedy bipartite bounding box matching at configurable IoU thresholds ($\tau = 0.5$) with precision, recall, and F1 calculation.
- **Zero-Fabrication Ground Truth Protocol**: Explicit `ground_truth_unavailable` status when references are missing—never fabricating false 0.0% metrics.
- **Publication Reporting**: Publication-grade Markdown tables, structured JSON, tabular CSV summaries, and headless Matplotlib visualization figures (`cer_wer_comparison.png`, `error_breakdown.png`).

---

## 2. Directory Structure

```
SIH26096/
├── configs/
│   └── e1_baseline.yaml              # Benchmark experiment configuration
├── data/
│   ├── ground_truth/                 # Verified human reference annotations
│   ├── manifests/                    # Document intake and rights manifests
│   ├── processed/
│   │   ├── pages/                    # 300 DPI rendered page PNGs & provenance
│   │   └── preprocessed/             # Intermediate filtered page images
│   └── raw/                          # Original archival PDFs and manuscripts
├── docs/
│   ├── STATE_AUDIT.md                # Comprehensive state audit & gap analysis
│   ├── DATASET_PROTOCOL.md           # Rights, scan quality tiers & sampling
│   ├── EXPERIMENT_PROTOCOL.md        # Controlled experiment variables & protocol
│   ├── IMPLEMENTATION_PLAN.md        # Architecture, data flows & E2/E3 contracts
│   ├── RESULTS.md                    # Measured benchmark results & integrity notes
│   ├── E1_OCR_RESULTS.md             # Empirical OCR benchmark status & Tesseract setup
│   ├── E2_RETRIEVAL_RESULTS.md       # IR benchmark architecture & gating status
│   ├── E3_ATTRIBUTION_RESULTS.md     # Grounded attribution architecture & refusal gate
│   └── RESEARCH_INTEGRITY.md         # Epistemic classification matrix
├── outputs/
│   ├── metrics/                      # Evaluated CER/WER & IoU metrics JSON/CSV
│   ├── ocr/                          # Standardized OCR token output JSON
│   └── reports/                      # Markdown report, CSV, and PNG charts
├── scripts/
│   ├── render_pdf.py                 # CLI: PDF to high-res image renderer
│   ├── run_ocr.py                    # CLI: OCR execution engine & preprocessor
│   ├── evaluate_ocr.py               # CLI: Standardized error evaluation engine
│   └── generate_report.py            # CLI: Publication report & chart generator
├── src/sih_archive/
│   ├── attribution/                  # Phase E3: Grounded claim synthesis & refusal
│   ├── evaluation/                   # Phase E1: CER/WER, IoU matching, reading order
│   ├── hardware/                     # Phase E5: Workstation, archival node, kiosk
│   ├── ingestion/                    # Phase E0: Intake audit and rights verification
│   ├── multilingual/                 # Phase E4: Translation and TTS adapters
│   ├── ocr/                          # Phase E1: Abstract adapter, Tesseract, Mock engines
│   ├── preprocessing/                # Phase E1: Grayscale, CLAHE, Otsu, Deskew, Denoise
│   ├── rendering/                    # Phase E1: PyMuPDF deterministic PDF rasterization
│   ├── retrieval/                    # Phase E2: BM25, N-Gram, Dense BGE-M3, Hybrid RRF
│   ├── schemas/                      # Core Pydantic v2 data models
│   └── utils/                        # Shared file and path utilities
├── tests/                            # Automated test suite (135 tests, 100% offline)
├── pytest.ini                        # Pytest configuration
├── requirements.txt                  # Minimal dependency specifications
└── README.md                         # Project overview and quickstart guide
```

---

## 3. Quickstart & Installation

### 3.1 Setup Environment

```bash
# Clone the repository
git clone https://github.com/GeekLuffy/SIH26096.git
cd SIH26096

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3.2 Automated Test Suite

Run the full automated test suite (runs 100% offline using synthetic fixtures without requiring external OCR binaries or large PDFs):

```bash
pytest tests/ -v
```

---

## 4. End-to-End Command Line Interface (CLI)

The framework includes 4 standardized CLI tools supporting full help documentation (`--help`).

### Step 1: Render Archival PDF (`scripts/render_pdf.py`)
Renders archival documents into 300 DPI page images with cryptographic provenance tracking and duplicate caching:

```bash
python scripts/render_pdf.py \
  --input data/raw/ambedkar_speech_vol1.pdf \
  --output data/processed/pages \
  --dpi 300 \
  --pages all
```
*Options*:
- `--input` / `-i`: Path to input PDF file or document manifest JSON.
- `--output` / `-o`: Output directory (default: `data/processed/pages`).
- `--dpi` / `-d`: Target rendering resolution (default: `300`).
- `--pages` / `-p`: Page selection (`'all'`, single number `'3'`, range `'1-3'`, or set `'1,3,5'`).
- `--force` / `-f`: Force re-rendering even if output images already exist.

### Step 2: Execute OCR with Preprocessing (`scripts/run_ocr.py`)
Executes OCR using an abstracted adapter (`mock` or `tesseract`) with optional image preprocessing pipelines:

```bash
python scripts/run_ocr.py \
  --input data/processed/pages/ambedkar_speech_vol1_p0001.png \
  --engine mock \
  --preprocess "grayscale,clahe" \
  --output outputs/ocr/ \
  --force
```
*Options*:
- `--input` / `-i`: Path to image file or directory containing page images.
- `--engine` / `-e`: OCR engine adapter (`'tesseract'` or `'mock'`, default: `tesseract`).
- `--language` / `-l`: ISO 639-3 language code (default: `eng`).
- `--preprocess` / `-p`: Comma-separated filter sequence (e.g. `'raw'`, `'clahe'`, `'grayscale,clahe,otsu'`).
- `--output` / `-o`: Output directory for OCR JSON files (default: `outputs/ocr`).
- `--check-only`: Verify engine availability and diagnostics without processing images.

### Step 3: Evaluate OCR Accuracy (`scripts/evaluate_ocr.py`)
Computes Levenshtein CER/WER edit distance breakdowns, greedy bipartite bounding box IoU, and Kendall's Tau reading order consistency:

```bash
python scripts/evaluate_ocr.py \
  --hypothesis outputs/ocr/ambedkar_speech_vol1_p0001_mock.json \
  --ground-truth data/ground_truth/ambedkar_speech_vol1_p0001.json \
  --output outputs/metrics/ \
  --iou-threshold 0.5 \
  --normalize \
  --format both
```
*Options*:
- `--hypothesis` / `-i`: Path to OCR hypothesis JSON file or directory.
- `--ground-truth` / `-g`: Path to Ground Truth JSON file or directory.
- `--output` / `-o`: Destination directory for metrics (default: `outputs/metrics`).
- `--iou-threshold`: Overlap threshold $\tau$ for bounding box matching (default: `0.5`).
- `--format`: Output format for summary report (`'json'`, `'csv'`, `'both'`).
- `--normalize`: Normalize contiguous whitespace and strip discretionary soft-hyphens.
- `--ignore-case`: Perform case-insensitive evaluation.

### Step 4: Generate Publication Benchmark Report (`scripts/generate_report.py`)
Compiles aggregated metrics into publication Markdown tables, structured JSON, tabular CSV summaries, and headless Matplotlib figures:

```bash
python scripts/generate_report.py \
  --metrics outputs/metrics/ \
  --output outputs/reports/ \
  --format all \
  --title "SIH26096 Archival OCR Benchmark Report (Phase E1)"
```
*Options*:
- `--metrics` / `-m`: Path to evaluation metrics JSON file or directory.
- `--output` / `-o`: Directory to save generated reports (default: `outputs/reports`).
- `--format` / `-f`: Report format (`'all'`, `'markdown'`, `'json'`, `'csv'`, `'chart'`).
- `--title`: Custom title header for publication report.

---

## 5. Downstream Phase Contracts

The schemas and artifacts generated by Phase E1 are explicitly designed for downstream compatibility:
- **Phase E2 (Lexical & Dense Retrieval)**: `OCROutput` records line and block numbers for context-aware passage chunking, word-level confidence scores to filter noisy tokens, and document IDs mapped to provenance manifests.
- **Phase E3 (Visual Citation Grounding)**: Word tokens in `OCROutput.regions` maintain absolute pixel bounding boxes `[x, y, w, h]`, allowing user-facing applications to draw highlight boxes directly on original archival scans.

---

## 6. Research Limitations & Hygiene Principles

1. **Host OCR Binaries**: If Tesseract is not installed on the host system, `TesseractAdapter` outputs truthful diagnostics with remediation commands rather than crashing or synthesizing dummy text. Development and CI rely on `MockOCRAdapter`.
2. **Reading Order Baseline**: Current reading order analysis employs a 1D Kendall's Tau rank correlation over matched bounding box centroids. Future work will extend this to 2D topological graph models.
3. **Double-Blind Ground Truth**: In compliance with our research protocol, only verified reference transcripts are quantitatively evaluated. Pages lacking verified annotations remain classified as `ground_truth_unavailable`.
