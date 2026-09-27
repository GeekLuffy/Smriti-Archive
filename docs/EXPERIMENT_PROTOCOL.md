# Experiment Protocol: Controlled Benchmarking of Archival OCR & Preprocessing

## 1. Research Objectives & Experimental Rationale

Under SIH 2026 Problem Statement SIH26096, historical archival manuscripts, government gazettes, and typed speeches exhibit severe physical degradation, including paper yellowing, ink bleed-through, uneven illumination, skewed scanning, and typography variations.

A common engineering assumption in document engineering is that image preprocessing filters (e.g., binarization, contrast normalization, smoothing) uniformly improve downstream OCR accuracy. However, in historical archives, aggressive thresholding or noise reduction frequently erodes delicate serif strokes, merges closely spaced characters, or eliminates faint historical diacritics.

This protocol defines a rigorous, controlled experiment to evaluate whether preprocessing filters objectively improve or impair OCR accuracy across degradation tiers.

---

## 2. Controlled Evaluation Variables

| Variable | Controlled Levels / Permutations | Notes |
| :--- | :--- | :--- |
| **Input Resolution** | 150 DPI (Tier 3 Degraded), 200 DPI (Tier 2 Microfilm), 300 DPI (Tier 1 Preservation) | Scaled deterministically from PDF points using PyMuPDF |
| **Preprocessing Pipelines** | 1. `raw` (RGB unprocessed baseline)<br>2. `grayscale,clahe` (Local contrast normalization)<br>3. `grayscale,clahe,otsu` (Adaptive contrast + Otsu binarization)<br>4. `denoise,clahe` (Non-local means smoothing + contrast)<br>5. `deskew,grayscale,otsu` (Orientation deskew + Otsu) | Filter sequence executed sequentially with tracked duration |
| **OCR Engines** | `tesseract` (v5 LSTM, PSM 3/6), `mock` (Deterministic baseline fixture) | Real engine status checked truthfully; mock used for CI |
| **Languages & Scripts** | `eng` (Latin), `mar` (Devanagari), `hin` (Devanagari) | ISO 639-3 language and ISO 15924 script codes |
| **Evaluation Metrics** | Character Error Rate (CER), Word Error Rate (WER), Bounding Box IoU F1, Reading Order | RapidFuzz Levenshtein editops and greedy bipartite IoU |

---

## 3. Scientific Hypotheses & Degradation Tiers

### 3.1 Hypothesis Formulations

- **Hypothesis $H_1$ (Contrast Enhancement on Faded Ink)**:  
  *On historical documents exhibiting low-contrast fading ($< 30$ grayscale dynamic range), applying CLAHE will reduce Character Error Rate (CER) by $\ge 15\%$ relative to raw RGB.*
- **Hypothesis $H_2$ (Over-Binarization on Thin Typography)**:  
  *On high-resolution clean scans (300 DPI, Tier 1), applying global Otsu binarization will increase character deletion errors ($D$) by $\ge 10\%$ due to stroke erosion on fine serif glyphs.*
- **Hypothesis $H_3$ (Deskew on Non-Orthogonal Scans)**:  
  *On scans rotated between $1.5^\circ$ and $5.0^\circ$, applying contour-based deskew correction prior to OCR will increase bounding box recall and reading order consistency by $\ge 20\%$.*

### 3.2 Physical Degradation Tiers

1. **Tier 1 (Preservation Grade)**:
   - Modern digital facsimile or high-resolution flatbed scan (300+ DPI).
   - Uniform illumination, sharp character edges, negligible skew ($< 0.5^\circ$), minimal bleed-through.
2. **Tier 2 (Archival / Microfilm Grade)**:
   - 200–300 DPI scans from microfilm aperture cards or aging paper prints (1920–1950).
   - Moderate paper yellowing, light bleed-through from reverse pages, slight skew ($0.5^\circ$ to $2.0^\circ$).
3. **Tier 3 (Severely Degraded Historical Manuscript)**:
   - $< 200$ DPI or heavily degraded 19th/early-20th-century originals.
   - Significant foxing spots, brittle paper tears, non-linear page curling, substantial skew ($> 2.0^\circ$).

---

## 4. Reproducible Execution Protocol

To reproduce the benchmark pipeline deterministically, follow these four standardized execution steps:

### Step 1: Ingestion & Rendering
Render target archival documents at 300 DPI to guarantee spatial resolution preservation:
```bash
python scripts/render_pdf.py \
  --input data/raw/ambedkar_speech_vol1.pdf \
  --output data/processed/pages \
  --dpi 300 \
  --pages all
```
*Verification*: Check that `ambedkar_speech_vol1_p0001.png` through `p0005.png` exist alongside page provenance manifests in `data/processed/pages/`.

### Step 2: Parametric OCR & Preprocessing Execution
Execute baseline and preprocessed variations across all target pages:
```bash
# Baseline: Unprocessed raw images
python scripts/run_ocr.py \
  --input data/processed/pages/ \
  --engine mock \
  --preprocess raw \
  --output outputs/ocr/ \
  --force

# Variation A: Grayscale + CLAHE contrast normalization
python scripts/run_ocr.py \
  --input data/processed/pages/ \
  --engine mock \
  --preprocess "grayscale,clahe" \
  --output outputs/ocr/ \
  --force

# Variation B: Grayscale + CLAHE + Otsu Binarization
python scripts/run_ocr.py \
  --input data/processed/pages/ \
  --engine mock \
  --preprocess "grayscale,clahe,otsu" \
  --output outputs/ocr/ \
  --force
```
*Verification*: Inspect `outputs/ocr/*.json` to confirm `processing.filters` matches the CLI arguments and `regions` contains word bounding boxes.

### Step 3: Standardized Error Metrics Evaluation
Evaluate OCR hypotheses against curated ground truth annotations:
```bash
python scripts/evaluate_ocr.py \
  --hypothesis outputs/ocr/ \
  --ground-truth data/ground_truth/ \
  --output outputs/metrics/ \
  --iou-threshold 0.5 \
  --normalize \
  --format both
```
*Verification*: Confirm `summary_metrics.json` and `summary_metrics.csv` are generated in `outputs/metrics/`, and unannotated pages are assigned `ground_truth_unavailable`.

### Step 4: Publication Report & Chart Generation
Synthesize metrics into publication markdown tables and headless Matplotlib figures:
```bash
python scripts/generate_report.py \
  --metrics outputs/metrics/ \
  --output outputs/reports/ \
  --format all \
  --title "SIH26096 Archival OCR Benchmark Report (Phase E1)"
```
*Verification*: Verify `benchmark_report.md`, `benchmark_report.json`, `benchmark_report.csv`, `cer_wer_comparison.png`, and `error_breakdown.png` are present in `outputs/reports/`.

---

## 5. Research Integrity Principles

1. **Zero-Fabrication Mandate**:
   - No benchmark results, metrics, transcripts, or confidence scores may ever be fabricated or hardcoded.
   - When external OCR engines (e.g. Tesseract) are absent from the host machine, the framework reports truthful diagnostics and does not synthesize dummy engine runs.
2. **Explicit Null Protocol for Unannotated Pages**:
   - Archival digitization frequently proceeds before complete transcription is available. Document pages lacking verified ground truth are explicitly marked `ground_truth_unavailable` with `cer: null`, `wer: null`, and `bbox_metrics: null`.
   - Never report 0.0% error rate for unverified pages.
3. **Hypothesis vs. Measured Data Demarcation**:
   - In all technical reports and publications, measured data on verified fixtures must be strictly separated from engineering hypotheses and prospective designs.
