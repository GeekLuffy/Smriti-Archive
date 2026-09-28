# SIH26096 — Master Experiment & Benchmark Status
**Problem Statement:** Digital Heritage Archive for Memorials, Manuscripts & Ambedkar: AI-Powered Institutional Archive and Audio-Visual Knowledge Platform  
**System State Date:** 2026-09-27  
**Repository:** `https://github.com/GeekLuffy/SIH26096`  
**Host Environment:** Windows (PowerShell, Python 3.11.9, pytest-9.0.2)  
**Research Engineering Lead:** Antigravity Research Team  

---

## 1. Executive Milestone Gate Status

| Milestone / Phase | Gate Status | Architecture Status | Empirical Status | Next Prerequisite to Unlock |
| :--- | :--- | :--- | :--- | :--- |
| **E0: Archival Corpus & Rights Intake** | **PASS (Intake & Provenance Metadata Validation: MEASURED)** | Complete & Tested | **VERIFIED (Metadata Protocol)** | Legal authorization for a specific corpus: NOT ESTABLISHED BY SOFTWARE TEST. Requires custodial institutional clearance for production deployment. |
| **E1: Archival OCR & Preprocessing Benchmark** | **BLOCKED** | Complete & Tested (`TesseractAdapter`, `MockOCRAdapter`, CLI, RapidFuzz CER/WER, IoU, Reading Order) | **BLOCKED ON HOST BINARY** | Install Tesseract OCR v5+ on host PATH with `eng`, `hin`, `mar` traineddata models + ingest physical degraded scan samples. |
| **E2: Resilient Retrieval Benchmark** | **LOCKED** | Complete Preview (`BM25`, `NGram-3`, `Dense BGE-M3 Mock`, `Hybrid RRF`) | **LOCKED PREVIEW** | Gated strictly on completion of empirical E1 on real archival scans. |
| **E3: Citation & Visual Attribution Grounding** | **LOCKED** | Complete Preview (`EvidenceGroundedAnswerPipeline`, Bounding Box Grounding, Refusal Engine) | **LOCKED PREVIEW** | Gated strictly on validated E1 and E2 outputs. |
| **E4: Multilingual Translation & Audio Synthesis** | **READY (Gated)** | Modeled (`TranslationAdapter`, `TTSAdapter`, Schemas) | **GATED** | Gated on E3 citation validation. |
| **E5: Institutional Deployment & Kiosk Hardware** | **READY (Gated)** | Modeled (`WorkstationConfig`, `ArchivalStorageNode`, `KioskController`) | **GATED** | Gated on field pilot approval. |

---

## 2. Research Integrity Audit & Status Classification

To avoid scientific fraud, premature performance claims, and simulation fallacies, all metrics across this repository are strictly classified into three categories:

1. **MEASURED**: Statistically computed against empirical, verifiable inputs with known ground truth and operational binaries.
2. **UNKNOWN**: Unmeasured characteristics (e.g. real OCR accuracy on degraded brittle paper) awaiting physical scans and local OCR execution.
3. **BLOCKED**: Experiments where code is fully implemented and passes unit tests, but execution is halted by external dependencies (e.g. system binary installation or admin elevation).

### Comprehensive Status Audit Table

| Component / Experiment | Classification | Empirical Value | Rationale & Evidence |
| :--- | :--- | :--- | :--- |
| **PDF Rasterization Pipeline** | **MEASURED** | 300 DPI, PyMuPDF, deterministic SHA-256 | Validated across 5 test pages with deterministic `{doc}_p{page:04d}` ID generation. |
| **Rights/Provenance Metadata Validation** | **MEASURED** | 100% compliant (schema & checksum verified) | Intake manifests record statutory citations; legal authorization for a specific corpus is NOT ESTABLISHED BY SOFTWARE TEST and requires institutional custodial confirmation. |
| **Tesseract Engine Host Presence** | **BLOCKED** | Not installed / Not in PATH | Windows UAC elevation prevented silent winget installation. Diagnostics accurately report binary absence. |
| **OCR Character Error Rate (CER) on Historical Scans** | **UNKNOWN** | Unknown | Current raw PDF (`ambedkar_speech_vol1.pdf`) is a synthetic digital vector PDF, NOT an authentic historical scan. |
| **OCR Word Error Rate (WER) on Historical Scans** | **UNKNOWN** | Unknown | Awaiting ingestion of authentic microfilms / degraded print scans. |
| **CLAHE / Otsu Preprocessing Benefit** | **UNKNOWN** | Unknown on historical scans | Filters implemented and tested on synthetic fixtures; empirical delta on historical ink bleed is unmeasured. |
| **Lexical vs Dense Retrieval on OCR Corrupted Text** | **UNKNOWN (Framework Preview)** | Simulated (Recall@10 = 1.0 on clean text) | Evaluated on mock/synthetic documents only. Official benchmark strictly LOCKED. |
| **Visual Bounding Box Citation Alignment** | **UNKNOWN (Framework Preview)** | Simulated (100% precision on mock query) | Algorithmic refusal and bounding box projection verified on synthetic tokens; real OCR noise unmeasured. |

---

## 3. Detailed Phase Status & Gating Criteria

### Phase E0: Archival Corpus & Rights Intake — `PASS`
- **Implemented:**
  - `src/sih_archive/schemas/manifest.py`: Strict Pydantic models for intellectual property tracking, checksums, and metadata.
  - `src/sih_archive/ingestion/protocol.py`: Path traversal sanitization, rights evidence enforcement, intake audit.
  - `scripts/ingest.py`: Multi-format CLI for PDF/image ingestion, metadata capture, and ground-truth transcript binding.
- **Verification:**
  - 144 unit and integration tests passing (`python -m pytest tests/ -v`).
  - Verified sample manifest `data/manifests/ambedkar_speech_vol1.json`.

### Phase E1: Archival OCR Benchmark — `BLOCKED`
- **Implemented:**
  - `src/sih_archive/ocr/base.py`, `src/sih_archive/ocr/tesseract.py`, `src/sih_archive/ocr/mock.py`.
  - `src/sih_archive/preprocessing/filters.py` (Grayscale, Resize, CLAHE, Otsu, Adaptive, Deskew, Denoise).
  - `src/sih_archive/evaluation/cer_wer.py` (RapidFuzz edit distance with S, D, I breakdowns).
  - `src/sih_archive/evaluation/iou.py` (Greedy bipartite bounding box IoU at $\tau=0.5$).
  - `src/sih_archive/evaluation/reading_order.py` (Kendall's Tau concordance).
  - `scripts/run_ocr.py`, `scripts/evaluate_ocr.py`, `scripts/generate_report.py`.
- **Blocking Bottleneck:**
  - Tesseract binary executable is not present on the host Windows PATH (`tesseract.exe`).
  - Downloaded installer (`tesseract-ocr-w64-setup-5.4.0.20240606.exe`) requires an interactive administrative prompt (UAC).
  - Physical historical manuscript scans with manual paleographic ground truth have not yet been placed in `data/raw/`.
- **Gating Rule to Unlock:**
  1. Install Tesseract 5.x on host system with English, Marathi (`mar`), and Hindi (`hin`) language packs.
  2. Ingest authentic historical scans into `data/raw/` with verified rights manifests.
  3. Execute `scripts/run_ocr.py` and `scripts/evaluate_ocr.py` to record genuine empirical CER/WER.

### Phase E2: Resilient Retrieval Benchmark — `LOCKED`
- **Implemented:**
  - `src/sih_archive/retrieval/bm25.py` (BM25 lexical index).
  - `src/sih_archive/retrieval/ngram.py` (Character 3-gram fuzzy index for OCR degradation tolerance).
  - `src/sih_archive/retrieval/dense.py` (Dense embedding abstraction, BGE-M3 ready, MockEmbeddingModel).
  - `src/sih_archive/retrieval/hybrid.py` (Reciprocal Rank Fusion at $k=60$).
  - `src/sih_archive/retrieval/metrics.py` (Recall@K, nDCG@K, MRR).
- **Locking Reason:**
  - Evaluating retrieval engines on clean, synthetic digital vector text produces misleading 100% recall figures that fail to simulate historical OCR degradation.
- **Unlocking Prerequisite:**
  - Unlocked automatically once empirical E1 OCR outputs from degraded historical scans are committed to `outputs/ocr/`.

### Phase E3: Attribution & Citation Grounding — `LOCKED`
- **Implemented:**
  - `src/sih_archive/attribution/pipeline.py` (`EvidenceGroundedAnswerPipeline` with token bounding-box mapping).
  - Strict algorithmic refusal mechanism returning explicit `insufficient_evidence` when query similarity falls below threshold $\tau_{\text{rel}}$.
  - `src/sih_archive/attribution/evaluator.py` (AttributionPrecision, CitationRecall, GroundingFaithfulness, RefusalAccuracy).
- **Locking Reason:**
  - Grounding faithfulness cannot be meaningfully verified on synthetic dummy citations without degraded OCR tokens.
- **Unlocking Prerequisite:**
  - Unlocked once empirical E1 tokens and E2 retrieval hits are validated.

### Phase E4: Multilingual Translation & Audio Synthesis — `READY (Gated)`
- **Implemented:**
  - `src/sih_archive/multilingual/base.py` (`TranslationAdapter`, `TTSAdapter`).
  - `src/sih_archive/multilingual/schemas.py` (`TranslationOutput`, `AudioOutput`, provenance tracking).
- **Gating Rule:**
  - Must not synthesize audio or translate text from unverified/unattributed source citations.

### Phase E5: Hardware & Institutional Deployment — `READY (Gated)`
- **Implemented:**
  - `src/sih_archive/hardware/schemas.py` (`WorkstationConfig`, `ArchivalStorageNode`, `KioskController`).
  - `src/sih_archive/hardware/interfaces.py` (Local archival server, offline kiosk, air-gapped sync specs).
- **Gating Rule:**
  - Hardware specifications will be finalized after empirical latency benchmarks on physical server nodes.

---

## 4. Machine-Readable Benchmark Outputs

The repository provides automated generation of standardized, machine-readable JSON benchmarks via `python scripts/run_benchmarks.py`:

- [`results/e1_ocr_results.json`](file:///F:/Projects/SIH26096/results/e1_ocr_results.json): Contains engine availability, host diagnostics, research integrity notices, and evaluated page metrics.
- [`results/e2_retrieval_results.json`](file:///F:/Projects/SIH26096/results/e2_retrieval_results.json): Contains locked preview benchmarks across BM25, Character 3-Gram, Dense, and Hybrid RRF.
- [`results/e3_attribution_results.json`](file:///F:/Projects/SIH26096/results/e3_attribution_results.json): Contains locked preview benchmarks for evidence grounding and refusal accuracy.

---

## 5. Summary of Automated Verification Suite

- **Total Passing Automated Tests:** 220 (100% pass rate)
- **Test Categories:**
  - Manifest & Rights Intake Protocol: 13 tests
  - PDF Rendering & Page Provenance: 15 tests
  - Preprocessing Filter Variations: 16 tests
  - OCR Adapters & Diagnostic Handling: 18 tests
  - CER / WER Edit Distance Evaluation: 12 tests
  - Bounding Box IoU & Reading Order: 14 tests
  - Reporting CLI & Visualization: 11 tests
  - Ingestion CLI & Benchmark Serialization: 9 tests
  - Retrieval Engines (BM25, N-Gram, Dense, Hybrid): 12 tests
  - Attribution Pipeline & Grounding Evaluation: 10 tests
  - Multilingual & Hardware Specs: 3 tests
  - Schema Roundtrips & Data Validation: 11 tests
  - Configuration & Storage Architecture: 4 tests
  - API Server, Security Gates & DEMO Mode: 14 tests
  - Vercel Serverless Entrypoint & Platform Adapters: 6 tests
  - Heritage Design System & Visual Hierarchy: 14 tests (`test_milestone2_heritage_ui.py`)
  - Manuscript Viewer & Evidence Bounding Boxes: 11 tests (`test_milestone3_viewer_assistant.py`)
  - Kiosk Mode, A/V Media Library & Institutional Admin: 14 tests (`test_milestone4_kiosk_admin_media.py`)
  - UI API Extensions (/kiosk, /media, /admin/audit, /provenance, /timeline): 13 tests (`test_ui_api_extensions.py`)
- **Execution Command:** `python -m pytest tests/ -v`
- **Execution Duration:** ~5.2 seconds

---

## 6. Multi-Tier Deployment Readiness vs. Empirical Validation Status

Deployment readiness and scientific validation status are strictly decoupled across tiers:

| Dimension | Engineering State | Empirical Scientific State | Action / Status |
| :--- | :--- | :--- | :--- |
| **Tier 1: Vercel Serverless Layer** | **READY** | N/A (Presentation) | `vercel.json` and `api/index.py` configured for public demo, search, and QA routing. |
| **Tier 2: Persistent Storage Layer** | **READY** | N/A (Infrastructure) | `ARCHIVE_DATA_DIR`, `GROUND_TRUTH_DIR`, `RESULTS_DIR`, `MODEL_CACHE_DIR` configurable via env vars. |
| **Tier 3: Northflank / On-Prem Compute** | **READY** | N/A (Infrastructure) | `Dockerfile`, non-root user (10001), health/readiness probes, dynamic `PORT`, persistent volume mapping tested. |
| **DEMO Mode Presentation** | **READY** | **SYNTHETIC PREVIEW** | Visibly labeled `⚠️ DEMO / SYNTHETIC DATA — NOT VALIDATED EMPIRICAL HISTORICAL RESULTS`. |
| **Phase E0 (Corpus / Rights)** | **READY** | **MEASURED (Metadata Validation)** | Rights/provenance metadata validation: MEASURED. Legal authorization for a specific corpus: NOT ESTABLISHED BY SOFTWARE TEST. |
| **Phase E1 (Archival OCR)** | **READY** | **BLOCKED ON HOST BINARY** | Engine adapter complete; awaiting host Tesseract binary on Windows/Linux and degraded scans. |
| **Phase E2 (Retrieval)** | **READY** | **STRICTLY LOCKED** | Benchmark locked until empirical E1 metrics on real scans are finalized. |
| **Phase E3 (Attribution)** | **READY** | **STRICTLY LOCKED** | Benchmark locked until empirical E1 and E2 outputs are validated. |

---

## 7. Verified Live Vercel Production Deployment

The public institutional presentation layer has been deployed to Vercel and verified across all live endpoints:

- **Production URL:** [https://orbit-heritage-archive.vercel.app](https://orbit-heritage-archive.vercel.app)
- **Deployment URL:** [https://orbit-heritage-archive-cbd0o2fgo-luffy-projects.vercel.app](https://orbit-heritage-archive-cbd0o2fgo-luffy-projects.vercel.app)
- **Project URL:** [https://vercel.com/luffy-projects/orbit-heritage-archive](https://vercel.com/luffy-projects/orbit-heritage-archive)
- **Deployment Status:** `READY` (HTTP 200)
- **Domain Privacy:** Old public aliases (`sih26096.vercel.app`, `sih26096-luffy-projects.vercel.app`) permanently unlinked and return 404 to protect team IP and research work.
- **Runtime:** Python 3.12.14 Serverless (`uv 0.10.11`) on `iad1` (Washington, D.C.)
- **Execution Mode:** `DEMO` (`platform_mode: vercel_serverless`)
- **Host OCR Status:** Truthfully reports `Tesseract available: false` (not bundled in Vercel serverless environment; reserved for Tier 3 Docker/Northflank compute).
- **Probes Verified:**
  - `GET /` -> HTTP 200 (Heritage Portal with hero, 6 discovery cards, and navigation)
  - `GET /kiosk` -> HTTP 200 (Touchscreen Museum Mode, min 48px touch targets, ambient display)
  - `GET /health` -> HTTP 200 (`{"status": "healthy", "service": "sih26096-archive", "execution_mode": "DEMO"}`)
  - `GET /ready` -> HTTP 200 (`{"status": "ready", "storage_ready": true, "is_serverless": true, "indexed_documents_count": 1}`)
  - `GET /api/v1/diagnostics` -> HTTP 200 (`platform_mode: vercel_serverless`, rights distinction preserved)
  - `GET /api/v1/search?q=Ambedkar` -> HTTP 200 (1 hit, score: 0.0328)
  - `POST /api/v1/qa` -> HTTP 200 (evidence-grounded answer with source quote and token bbox)
  - `GET /api/v1/benchmarks/e1` -> HTTP 200 (`gate_status: BLOCKED_ON_HOST_OCR_BINARY`)
  - `GET /api/v1/benchmarks/e2` -> HTTP 200 (`gate_status: LOCKED_PREVIEW`)
  - `GET /api/v1/benchmarks/e3` -> HTTP 200 (`gate_status: LOCKED_PREVIEW`)
  - `GET /api/v1/media` -> HTTP 200 (A/V Media Library with 3 archival records & time-coded transcripts)
  - `GET /api/v1/admin/audit` -> HTTP 200 (Institutional Admin audit reporting operational health)
  - `GET /api/v1/provenance/ambedkar_speech_vol1_p0001` -> HTTP 200 (6-stage cryptographic custody chain)
  - `POST /api/v1/ingest` (5MB / 4.2MB) -> HTTP 413 (Vercel edge cutoff & controlled 4MB app limit with clear serverless guidance)


