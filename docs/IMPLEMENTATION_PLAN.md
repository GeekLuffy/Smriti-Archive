# Implementation Plan: SIH26096 Archival OCR Benchmarking & Digital Heritage Framework

## 1. Overview & Problem Scope

**Problem Statement**: SIH26096 — Digital Heritage Archive for Memorials, Manuscripts & Ambedkar  
**Target Domain**: Historical institutional archives, rare print editions, typed government proceedings, and handwritten archival manuscripts.  
**System Objective**: Provide an end-to-end, reproducible, research-grade OCR benchmarking and provenance preservation pipeline (Phases E0 and E1). The framework establishes tamper-evident ingestion, deterministic high-resolution rasterization, modular image preprocessing, OCR engine abstraction, edit-distance error decomposition, geometric layout evaluation, and publication-ready reporting—without premature production shortcuts or fabricated benchmark data.

```
       [ Phase E0: Ingestion & Rights ]
             │
             ▼
       [ Phase E1: Ingestion / Rendering ]
             │
             ├──► Deterministic Rendering (PyMuPDF, 300 DPI, {doc}_p{page:04d})
             ├──► Preprocessing Pipeline (Grayscale, CLAHE, Otsu, Deskew, Denoise)
             ├──► Common OCR Adapter (Tesseract / Mock / Future TrOCR)
             ├──► Standardized Evaluation (RapidFuzz CER/WER, Greedy IoU, Kendall Tau)
             └──► Publication Reporting (Markdown tables, JSON, CSV, Headless Charts)
             │
             ▼
  ┌────────────────────────────────────────────────────────┐
  │ Downstream Compatibility Interfaces                    │
  │                                                        │
  │  ► Phase E2: Lexical & Dense Retrieval Indexes         │
  │  ► Phase E3: Multi-modal Citation & Region Grounding   │
  └────────────────────────────────────────────────────────┘
```

---

## 2. Phase Definitions

### 2.1 Phase E0: Archival Corpus Intake & Rights Hygiene
- **Purpose**: Prevent legal, intellectual property, and data integrity hazards before computational processing.
- **Components**:
  - `DocumentManifest` schema (Pydantic v2): Tracks `document_id`, `source_url`, `source_organization`, `language` (ISO 639-3), `script` (ISO 15924), `rights_status` (`public`, `verified`, `restricted`, `unknown`), `rights_evidence`, `local_path`, and `sha256`.
  - `sih_archive.ingestion.protocol`: Enforces that raw assets reside exclusively within `data/raw/`, validates physical file integrity against SHA-256 cryptographic hashes, blocks path traversal attempts, and conducts intake audits (`audit_intake`).
  - `docs/DATASET_PROTOCOL.md`: Establishes statutory copyright frameworks (Indian Copyright Act 1957, Section 52(1)(q)), scan quality classification (Tiers 1–3), stratified page sampling protocols (Strata A–E), and double-blind transcription standards.

### 2.2 Phase E1: Deterministic Rendering, Preprocessing, OCR & Standardized Evaluation
- **Purpose**: Establish empirical, reproducible measurement of OCR accuracy on archival documents.
- **Components**:
  - **Deterministic Rendering (`sih_archive.rendering.pdf`)**: Converts vector/scanned PDFs into 300 DPI 24-bit RGB PNG page images with `{document_id}_p{page_num:04d}.png` naming, page-level provenance manifests, and duplicate rendering cache detection.
  - **Modular Preprocessing (`sih_archive.preprocessing.filters`)**: Extensible filter pipeline (`Grayscale`, `Resize`, `CLAHE`, `Threshold`, `Deskew`, `Denoise`) measuring whether pre-filtering objectively enhances or degrades character recognition.
  - **Common OCR Adapter (`sih_archive.ocr.base`)**: Uniform interface (`OCRAdapter`) abstracting OCR execution. Preserves word-level token bounding boxes `[x, y, w, h]`, line/block hierarchy, text, and confidence scores. Provides truthful missing-engine diagnostics (`TesseractAdapter`) and isolated CI test execution (`MockOCRAdapter`).
  - **Standardized Error Metrics (`sih_archive.evaluation`)**:
    - Character Error Rate (CER) and Word Error Rate (WER) via RapidFuzz Levenshtein edit operations, decomposed into exact substitutions ($S$), deletions ($D$), and insertions ($I$).
    - Geometric bounding box matching via greedy bipartite overlap at IoU threshold $\tau = 0.5$ (precision, recall, F1, mean IoU).
    - Reading order sequence evaluation via normalized Kendall's Tau rank correlation.
    - Zero-fabrication `"ground_truth_unavailable"` protocol for pages lacking reference transcripts.
  - **Publication Reporting (`scripts/generate_report.py`)**: Markdown benchmark summaries, structured JSON, tabular CSV, and headless Matplotlib charts (`cer_wer_comparison.png`, `error_breakdown.png`).

---

## 3. Architecture & Data Flow

| Stage | Input Artifact | Processing Module | Output Artifact | Telemetry / Provenance Tracked |
| :--- | :--- | :--- | :--- | :--- |
| **1. Intake** | `data/raw/*.pdf` | `sih_archive.ingestion` | `data/manifests/*.json` | File size, SHA-256, Rights status, Legal evidence |
| **2. Render** | `data/raw/*.pdf` | `sih_archive.rendering` | `data/processed/pages/*.png` | DPI, point-to-pixel scale, source PDF SHA-256 |
| **3. Preprocess** | `data/processed/pages/*.png` | `sih_archive.preprocessing` | `data/processed/preprocessed/*.png` | Filter list, parameter dict, execution duration ms |
| **4. OCR** | Page Image (`.png`) | `sih_archive.ocr` | `outputs/ocr/*.json` | Engine version, token bboxes, confidence, duration ms |
| **5. Evaluate** | Hypothesis & Ground Truth | `sih_archive.evaluation` | `outputs/metrics/*.json`, `.csv` | Editops (S, D, I), IoU matches, Kendall Tau score |
| **6. Report** | `outputs/metrics/` | `scripts/generate_report.py` | `outputs/reports/*.md`, `*.json`, `*.png` | Aggregated means, per-pipeline comparisons, plots |

---

## 4. Evaluation Methodology

### 4.1 Levenshtein Edit Operation Decomposition
Rather than treating edit distance as an opaque integer, our evaluation decomposes string transformation operations into:
$$\text{CER} = \frac{S + D + I}{N}$$
where:
- $S$: Character Substitutions (misidentified graphemes / glyphs)
- $D$: Character Deletions (faint, eroded, or broken characters skipped by the engine)
- $I$: Character Insertions (spurious characters hallucinated from bleed-through, paper foxing, or scanning artifacts)
- $N$: Total characters in the verified ground truth reference string

Word Error Rate (WER) uses identical edit-distance mechanics over whitespace-tokenized word sequences. Normalization collapses multi-spaces and eliminates discretionary soft hyphens (`\u00ad`) to prevent typographic penalties.

### 4.2 Geometric Region Matching (Greedy Bipartite IoU)
Given hypothesis bounding boxes $\mathcal{H} = \{h_1, \dots, h_m\}$ and ground truth reference boxes $\mathcal{R} = \{r_1, \dots, r_n\}$:
1. Compute pairwise Intersection over Union:
   $$\text{IoU}(h_i, r_j) = \frac{\text{Area}(h_i \cap r_j)}{\text{Area}(h_i \cup r_j)}$$
2. Filter pairs with $\text{IoU} \ge \tau$ (default $\tau = 0.5$).
3. Sort candidate pairs descending by IoU score.
4. Greedily match pairs without replacement, prioritizing maximal overlap.
5. Compute precision, recall, and F1:
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad \text{F1} = \frac{2 \cdot P \cdot R}{P + R}$$

### 4.3 Reading Order Consistency (Kendall's Tau)
For matched region pairs sorted by reference reading order $\pi_{\text{ref}}$, calculate the number of concordant pairs $C$ and discordant pairs $D$ in hypothesis order $\pi_{\text{hyp}}$:
$$\tau = \frac{C - D}{\frac{1}{2} n (n - 1)}$$
The score is mapped to a normalized interval $[0, 1]$ via $\text{Score} = \frac{\tau + 1}{2}$, serving as an evolving research baseline.

### 4.4 Research Integrity Protocol: Ground Truth Unavailable
When evaluating document pages where reference transcriptions have not been double-keyed or verified, the system strictly outputs:
```json
{
  "status": "ground_truth_unavailable",
  "cer": null,
  "wer": null,
  "cer_breakdown": null,
  "wer_breakdown": null,
  "bbox_metrics": null,
  "reading_order_score": null,
  "message": "Ground truth unavailable: no reference annotation found..."
}
```
**No synthetic 0.0% metrics, dummy transcripts, or interpolated values are permitted.**

---

## 5. Downstream Integration Contracts

To ensure that the Phase E1 benchmarking foundation seamlessly powers future search and grounded Q&A capabilities, the following explicit integration contracts are established:

### 5.1 Phase E2: Lexical & Dense Retrieval Integration Contract

Phase E2 will build BM25 lexical indexes and dense neural vector embeddings over archival text. The OCR output schema (`OCROutput`) provides direct support:

1. **Chunking & Passage Boundaries**:
   - `OCROutput.regions` contains `block_num` and `line_num` hierarchy fields.
   - Downstream indexers can construct contiguous paragraphs using block boundaries rather than arbitrary sliding token windows, preserving historical narrative coherence.
2. **Confidence-Weighted Indexing**:
   - Each `TokenRegion` carries a calibrated `confidence: float \in [0.0, 100.0]`.
   - Lexical tokenizers can down-weight or flag low-confidence tokens ($< 60.0$) to prevent index pollution from noisy OCR hallucinations.
3. **Document Provenance**:
   - `OCROutput.document_id` and `OCROutput.page_id` directly map to `DocumentManifest` and `PageProvenance`, ensuring every retrieved passage links to its statutory rights license and source PDF SHA-256.

```json
{
  "contract_type": "Phase_E2_Retrieval_Payload",
  "document_id": "ambedkar_speech_vol1",
  "page_id": "ambedkar_speech_vol1_p0001",
  "passage_id": "ambedkar_speech_vol1_p0001_b0001",
  "text": "SPEECHES OF DR. BABASAHEB AMBEDKAR",
  "mean_confidence": 96.5,
  "source_image": "data/processed/pages/ambedkar_speech_vol1_p0001.png",
  "rights_status": "public"
}
```

### 5.2 Phase E3: Citation Grounding & Visual Highlighting Contract

Phase E3 will provide multi-modal citation grounding, enabling user-facing applications to substantiate AI answers by drawing bounding boxes directly on original archival scans:

1. **Exact Bounding Box Coordinates**:
   - Every word token in `OCROutput.regions` records `bbox: [x, y, w, h]` in absolute pixel coordinates at the rendered resolution (300 DPI).
2. **Normalized Coordinate Transformation**:
   - Downstream user interfaces can convert pixel coordinates to responsive normalized canvas coordinates via:
     $$x_{\text{norm}} = \frac{x}{\text{width}}, \quad y_{\text{norm}} = \frac{y}{\text{height}}, \quad w_{\text{norm}} = \frac{w}{\text{width}}, \quad h_{\text{norm}} = \frac{h}{\text{height}}$$
   - Page dimensions are permanently tracked in `PageProvenance` (`width`, `height`, `orig_width_pt`, `orig_height_pt`).
3. **Audit Trail Verification**:
   - The citation engine verifies that the rendered page image has not been altered by matching its SHA-256 hash against `PageProvenance.sha256`.

```json
{
  "contract_type": "Phase_E3_Citation_Grounding",
  "claim_text": "Castes in India: Their Mechanism, Genesis and Development",
  "citation": {
    "document_id": "ambedkar_speech_vol1",
    "page_id": "ambedkar_speech_vol1_p0002",
    "image_path": "data/processed/pages/ambedkar_speech_vol1_p0002.png",
    "bounding_boxes": [
      {"word": "Castes", "bbox": [180, 420, 115, 38], "confidence": 98.2},
      {"word": "in", "bbox": [305, 420, 35, 38], "confidence": 99.0},
      {"word": "India", "bbox": [350, 420, 95, 38], "confidence": 98.5}
    ],
    "provenance_hash": "f085dd782a7bc0f82df977a16b9cb8bc9ee81bfd8c9735d6480f2d47ca6caea9"
  }
}
```
