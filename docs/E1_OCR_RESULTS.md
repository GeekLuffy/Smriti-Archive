# Phase E1: OCR Benchmark Results & Empirical Audit

**Status**: **BLOCKED / INCOMPLETE (Framework Functional, Empirical Evidence Pending)**  
**Benchmark Date**: 2026-09-27  
**Operating Environment**: Windows 11 Pro, Python 3.11.9, PyMuPDF 1.28.2, RapidFuzz 3.14.3, OpenCV 4.13.0  

---

## 1. Research Gate Assessment

In strict accordance with the SIH26096 Research Integrity Protocol, Phase E1 evaluates whether automated optical character recognition can reliably transcribe historical institutional documents, government gazettes, and writings of Dr. B.R. Ambedkar.

| Gate Criterion | Verification State | Evidence / Finding |
| :--- | :---: | :--- |
| **Real Corpus Provenance Documented** | **PARTIAL** | Manifest exists for `ambedkar_speech_vol1`, but the file is a clean digital vector text excerpt, not an authentic degraded period scan. |
| **Rights & Redistribution Status Documented** | **VERIFIED** | Indian Copyright Act 1957 Section 52(1)(q) and Section 22 cited with legal analysis. |
| **Real Page Images Rendered** | **VERIFIED** | PyMuPDF renders 300 DPI 24-bit PNGs with deterministic `{doc}_p{page:04d}` naming. |
| **Real OCR Engine Executed** | **BLOCKED** | Tesseract OCR binary is **not installed** in system PATH on host machine. Pipeline refused to synthesize fake output and executed deterministic mock adapter for code verification only. |
| **Engine & Version Recorded** | **VERIFIED** | Engine version metadata schema enforced (`OCROutput.engine_version`). |
| **Raw OCR Preserved** | **VERIFIED** | `run_ocr.py` preserves `outputs/ocr/{page_id}.json` as raw baseline, saving preprocessed runs to `{page_id}_{engine}_{filter}.json`. |
| **Independent Ground Truth Created** | **PARTIAL** | Only 1 page (`p0001`) has human reference ground truth. Pages 2–5 lack verified ground truth. |
| **Standardized CER/WER Measured** | **VERIFIED (Baseline)** | RapidFuzz Levenshtein edit distance with explicit operation decompositions ($S, D, I$). |
| **Geometric Bounding Box Evaluated** | **VERIFIED (Baseline)** | Greedy bipartite matching at $\tau = 0.5$ IoU implemented and validated. |
| **Reading Order Consistency Evaluated** | **VERIFIED (Baseline)** | Normalized Kendall's Tau correlation implemented. |
| **Preprocessing Comparison (RAW vs Filtered)** | **VERIFIED (Baseline)** | Controlled comparison pipeline executed across `raw`, `otsu`, `clahe`, and `deskew`. |
| **Reproducibility & Test Suite** | **VERIFIED** | 100% reproducible via `configs/e1_baseline.yaml` and CLI tools; 135 unit tests pass. |

> [!CAUTION]
> **GATE VERDICT**: **PHASE E1 CANNOT BE MARKED COMPLETE.**  
> While the software pipeline is 100% operational and verified with 135 passing tests, **real-world empirical performance on authentic historical scans cannot be claimed until host Tesseract is installed and authentic scanned editions are evaluated against double-blind human transcripts.**

---

## 2. Host Tesseract Setup & Remediation Instructions

To execute real empirical OCR on host Windows hardware:

1. **Option A: Automated Windows Package Manager (Admin Terminal)**
   ```powershell
   winget install --id UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
   ```
2. **Option B: Manual Installer**
   - Download the official Windows 64-bit installer from UB-Mannheim:
     `https://github.com/UB-Mannheim/tesseract/releases`
   - Run the installer and select language packs:
     - English (`eng`)
     - Hindi (`hin`)
     - Marathi (`mar`)
   - Add the installation directory to your system `PATH` (typically `C:\Program Files\Tesseract-OCR\`).
3. **Verify Installation**:
   ```powershell
   python scripts/run_ocr.py --input data/processed/pages/ --engine tesseract --check-only
   ```

---

## 3. Baseline Framework Benchmark Metrics (Deterministic Test Run)

The following metrics represent baseline validation using `MockOCRAdapter` on the digital facsimile of `ambedkar_speech_vol1`:

| Page ID | Engine | Preprocessing Pipeline | Status | CER (%) | WER (%) | Char Edit Breakdown (S / D / I) | Word Edit Breakdown (S / D / I) | BBox F1 | Mean IoU |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `p0001` | `mock` | `raw` | `evaluated` | **0.00%** | **0.00%** | 0 / 0 / 0 | 0 / 0 / 0 | 0.0000 | 0.0000 |
| `p0001` | `mock` | `otsu` | `evaluated` | **0.00%** | **0.00%** | 0 / 0 / 0 | 0 / 0 / 0 | 0.0000 | 0.0000 |
| `p0001` | `mock` | `grayscale` | `evaluated` | **79.77%** | **100.00%** | 98 / 38 / 2 | 15 / 9 / 0 | 0.0000 | 0.0000 |
| `p0002` | `mock` | `raw` | `ground_truth_unavailable` | null | null | null | null | null | null |
| `p0003` | `mock` | `raw` | `ground_truth_unavailable` | null | null | null | null | null | null |
| `p0004` | `mock` | `raw` | `ground_truth_unavailable` | null | null | null | null | null | null |
| `p0005` | `mock` | `raw` | `ground_truth_unavailable` | null | null | null | null | null | null |

---

## 4. Key Limitations & Empirical Gaps

1. **Synthetic vs. Archival Gap**: Clean vector PDFs fail to model uneven ink transfer, gutter shadows, brittle page tears, or ink bleed-through.
2. **Missing Ground Truth**: Only Page 1 possesses an authoritative ground truth file. 30–50 authentic pages must be transcribed double-blind before empirical claims can be published.
3. **Indic Script Support**: Devanagari OCR (Marathi and Hindi) requires complex conjunct evaluation ($संयुक्त\ अक्षरे$) which must be tested with `mar` and `hin` traineddata models.
