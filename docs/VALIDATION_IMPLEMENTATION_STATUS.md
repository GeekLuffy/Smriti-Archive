# SIH26096 — Empirical Validation Implementation Status
**System:** Digital Heritage Archive for Memorials, Manuscripts & Ambedkar: AI-Powered Institutional Archive  
**Team:** ORBIT  
**Audit Date:** 2026-09-29  
**Current Test Status:** **238/238 passing automated tests (100%)**  
**Scientific Gating Status:** E0: `MEASURED` | E1: `BLOCKED_ON_HOST_OCR_BINARY` | E2: `LOCKED_PREVIEW` | E3: `LOCKED_PREVIEW`  
**Research Integrity Protocol:** Strict separation between `MEASURED`, `BLOCKED`, and `LOCKED_PREVIEW`. Never fabricate empirical data or claim historical accuracy on synthetic vector fixtures.

---

## 1. Executive Implementation Audit

The empirical validation pipeline has been implemented across dedicated research benchmark scripts, structured evaluation datasets, and terminal dashboards:

| Milestone / Phase | Gate Status | Implemented Component | Empirical State | Unlock Condition |
| :--- | :--- | :--- | :--- | :--- |
| **E0: Archival Corpus & Rights Intake** | **MEASURED** | `src/sih_archive/ingestion/protocol.py`, `scripts/ingest.py`, manifests in `data/manifests/` | **VERIFIED (Metadata Protocol)** | Software test validates statutory citations and rights metadata. Custodial institutional clearance required for specific corpus legal authorization. |
| **E1: Real Archival OCR Benchmark** | **BLOCKED_ON_HOST_OCR_BINARY** | `scripts/run_e1_ocr.py`, `src/sih_archive/ocr/tesseract.py`, `src/sih_archive/preprocessing/filters.py` | **BLOCKED ON HOST BINARY & SCANS** | 1. Install Tesseract OCR v5+ with `eng`, `hin`, `mar` on host PATH.<br>2. Ingest 30–50 authentic degraded archival scans into `data/raw/` with independent ground truth. |
| **E2: Resilient Retrieval Benchmark** | **LOCKED_PREVIEW** | `scripts/run_e2_retrieval.py`, `BM25`, `Character 3-Gram`, `Dense BGE-M3 (Mock)`, `Hybrid RRF (k=60)`, `data/evaluation/judged_queries.json` | **LOCKED PREVIEW** | Gated strictly on empirical E1 completion on authentic degraded scans. |
| **E3: Evidence Attribution & Refusal** | **LOCKED_PREVIEW** | `scripts/run_e3_attribution.py`, `EvidenceGroundedAnswerPipeline`, `data/evaluation/attribution_questions.json` | **LOCKED PREVIEW** | Gated strictly on empirical completion of Phases E1 and E2. |

---

## 2. Implemented Tooling & Verification Capabilities

### 2.1 Dedicated Empirical Benchmark Runners

1. **`scripts/run_e1_ocr.py` (Phase E1 Archival OCR Pipeline):**
   - Truthful host Tesseract binary detection without simulation.
   - Configurable target language models (`eng`, `hin`, `mar`).
   - Configurable preprocessing filter variations: `raw`, `grayscale`, `denoise`, `deskew`, `adaptive_gaussian`, `all`.
   - Full evaluation metrics: RapidFuzz Levenshtein Character Error Rate (CER), Word Error Rate (WER) with exact S/D/I decompositions, Kendall's Tau reading order concordance, and greedy bipartite bounding-box IoU ($\tau=0.5$).
   - Explicit `ground_truth_unavailable` handling: if ground truth is absent, marks page status honestly without faking scores.
   - Strict gating: if host Tesseract binary is absent, halts with `BLOCKED_ON_HOST_OCR_BINARY` and generates diagnostic reports in `results/e1/`.
   - Emits: `e1_benchmark_report.json`, `summary_metrics.csv`, `REPORT.md`, `config_snapshot.json`, `dataset_manifest.json`.

2. **`scripts/run_e2_retrieval.py` (Phase E2 Resilient Retrieval Pipeline):**
   - Checks upstream E1 status: if E1 is not `MEASURED` on real scans, preserves `LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1)`.
   - Compares 4 retrieval paradigms:
     1. Lexical BM25 (clean keyword search)
     2. Character 3-Gram Fuzzy (OCR noise & character corruption tolerance)
     3. Dense Semantic (BGE-M3 / semantic concept matching)
     4. Hybrid Reciprocal Rank Fusion ($k=60$)
   - Uses graded relevance benchmark (`data/evaluation/judged_queries.json`).
   - Measures: Recall@10, nDCG@10, Mean Reciprocal Rank (MRR), Mean Latency (ms), and Index Size (tokens/pages).
   - Core research principle: **No Universal Winner**. Recognizes that optimal retrieval is document-condition dependent.
   - Emits: `e2_retrieval_results.json`, `retrieval_comparison.csv`, `REPORT.md`, `config_snapshot.json`.

3. **`scripts/run_e3_attribution.py` (Phase E3 Evidence Attribution Pipeline):**
   - Checks upstream E1 and E2 status: enforces `LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1 and E2)`.
   - Traces complete chain: `Question -> Retrieved Evidence -> Generated Answer -> Supporting Span -> Page -> Region/BBox`.
   - Measures: Claim Support Rate, Span Precision, BBox IoU, Broken-Citation Rate, and Unsupported Answer Rate.
   - Principled algorithmic refusal: generates *"Insufficient archival evidence found for a supported answer"* when primary evidence is absent or similarity falls below threshold $\tau_{\text{rel}}$.
   - Dual-annotator agreement: supports two independent human annotators and computes percent agreement and Cohen's Kappa.
   - Emits: `e3_attribution_results.json`, `annotator_agreement.json`, `REPORT.md`, `config_snapshot.json`.

4. **`scripts/validation_status.py` (Institutional Gating Dashboard CLI):**
   - Terminal status display and machine-readable JSON (`--json`) inspecting all 4 research gates.
   - Detects host OCR binary and language models.
   - Reports exact blockers and actionable CLI remediation steps.

---

## 3. Exact Dataset Requirements to Unlock Validation

### Phase E1 (OCR Benchmark):
- **Target Volume:** 30–50 authentic degraded manuscript/record pages.
- **Language Coverage:** English, Hindi (`hin`), and Marathi (`mar`).
- **Required Metadata Per Sample:**
  - `document_id`: Source archival volume identifier.
  - `page_id`: Deterministic page identifier (`{document_id}_p{page_num:04d}`).
  - `image`: High-resolution raster scan (300 DPI PNG/TIFF).
  - `rights_metadata`: Statutory citation and rights status.
  - `ground_truth_transcription`: Independent human-curated paleographic reference transcription (never generated from the OCR engine being tested).

### Phase E2 (Retrieval Benchmark):
- **Target Volume:** 100–200 indexed archival pages.
- **Judged Queries:** 50 realistic historical research queries representing real archival inquiries with 4-level graded relevance (0 = irrelevant, 1 = marginal, 2 = substantial, 3 = primary evidence).

### Phase E3 (Evidence Attribution Benchmark):
- **Target Volume:** 30–50 pages, ~50 complex research questions.
- **Annotators:** 2 independent human domain reviewers scoring claim support, span precision, and refusal appropriateness.

---

## 4. Exact Execution Commands

```bash
# 1. Inspect overall institutional validation status
python scripts/validation_status.py
python scripts/validation_status.py --json

# 2. Check E1 host environment dependencies without processing
python scripts/run_e1_ocr.py --check-only

# 3. Execute Phase E1 Archival OCR Benchmark
python scripts/run_e1_ocr.py \
  --input data/processed/pages \
  --output results/e1 \
  --languages eng hin mar \
  --preprocessing all \
  --ground-truth data/ground_truth

# 4. Execute Phase E2 Resilient Retrieval Benchmark
python scripts/run_e2_retrieval.py \
  --input-ocr outputs/ocr \
  --e1-results results/e1/e1_benchmark_report.json \
  --queries data/evaluation/judged_queries.json \
  --output results/e2

# 5. Execute Phase E3 Evidence Attribution Benchmark
python scripts/run_e3_attribution.py \
  --input-ocr outputs/ocr \
  --e1-results results/e1/e1_benchmark_report.json \
  --e2-results results/e2/e2_retrieval_results.json \
  --questions data/evaluation/attribution_questions.json \
  --output results/e3

# 6. Run complete automated test suite (238 tests)
python -m pytest tests/ -v
```

---

## 5. Current Primary Blocker to Unlock Phase E1

1. **Host Tesseract OCR Binary:**
   - Diagnostic: `Tesseract OCR binary not found. Searched: env TESSERACT_CMD/TESSERACT_PATH, system PATH lookup, C:\Program Files\Tesseract-OCR\tesseract.exe...`
   - Action Required: Install Tesseract 5.x on host PATH with `eng`, `hin`, and `mar` traineddata packs (`winget install UB-Mannheim.TesseractOCR` or Linux `sudo apt-get install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar`).
2. **Archival Corpus Authenticity:**
   - Current sample is a synthetic digital vector PDF excerpt (`ambedkar_speech_vol1.pdf`, 5 pages).
   - Action Required: Supply 30–50 pages of authentic degraded print/manuscript scans into `data/raw/` with independent ground-truth JSON files in `data/ground_truth/`.
