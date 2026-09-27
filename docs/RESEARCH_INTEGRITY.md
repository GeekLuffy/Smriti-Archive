# Research Integrity & Epistemic Demarcation Charter

**Project**: SIH 2026 Problem Statement SIH26096  
**Document Version**: 1.0.0  
**Enforcement**: Mandatory across all documentation, benchmarking, and code  

---

## 1. Core Principles of Research Integrity

To ensure that the digital heritage archive developed for **SIH26096** is grounded in scientific rigor rather than unsubstantiated claims or AI-generated hyperbole, every technical assertion made in this repository is strictly categorized into one of five epistemic tiers:

```
[ Tier A: Verified Facts ] ──────────► Legal statutes, official catalog data, physical document properties
[ Tier B: Measured Results ] ────────► Directly computed metrics from executable code on disk
[ Tier C: Engineering Assumptions ] ─► Pragmatic architectural decisions (DPI, thresholds, RRF k)
[ Tier D: Team-Defined Protocols ] ──► Experimental frameworks (Tiers 1-3, Strata A-E)
[ Tier E: Unresolved Questions ] ────► Empirical gaps requiring further experimentation
```

---

## 2. Epistemic Classification Matrix

### Tier A: Verified Facts (Source-Derived and Statutory Truths)
1. **Author Copyright Expiry**: Dr. B.R. Ambedkar passed away in December 1956. Under the *Indian Copyright Act, 1957, Section 22*, copyright in published literary works expires 60 years post-mortem (effective January 1, 2017).
2. **Official Government Proceedings**: Under Section 52(1)(q) of the Indian Copyright Act, reproduction of legislative assembly debates, official reports, and committee publications is statutory non-infringement.
3. **Repository Environment Reality**: Python 3.11.9, Windows 11, and PyMuPDF 1.28.2 are physically installed and verified on the host system.
4. **Binary Availability Reality**: Tesseract OCR is currently **not present in system PATH** on the host operating system.

### Tier B: Measured Results (Empirically Obtained)
1. **Automated Test Suite**: Exactly **135 test cases** pass across 12 test modules in 3.96 seconds (`python -m pytest tests/ -v`).
2. **Deterministic Rendering**: Vector rendering of `ambedkar_speech_vol1.pdf` at 300 DPI produces exactly 5 PNG images of dimensions $2480 \times 3509$ pixels with SHA-256 integrity verification.
3. **CER / WER Edit Breakdown**: Character Error Rate and Word Error Rate on Page 1 (`p0001`) under `MockOCRAdapter` measured 0.00% across raw and otsu pipelines, and 79.77% CER / 100.00% WER under the degraded mock pipeline, confirming the mathematical accuracy of the RapidFuzz Levenshtein editops counter.
4. **Retrieval Latency Baseline**: BM25, Character N-Gram, and Dense Mock retrieval execute within 15 ms on in-memory mock document indices.

### Tier C: Engineering Assumptions (Pragmatic Design Choices)
1. **Resolution Choice (300 DPI)**: Adopted as the pragmatic default resolution for character recognition. It balances optical character size with memory efficiency; it is **not** claimed to be universally optimal for all historical media.
2. **Greedy Bipartite IoU ($\tau = 0.5$)**: Chosen based on standard object detection literature (PASCAL VOC / COCO standards) for matching word-level token bounding boxes.
3. **RRF Constant ($k = 60$)**: Adopted from Cormack et al. (2009) as the standard reciprocal rank fusion smoothing constant.
4. **Refusal Thresholds**: Set to 0.1 minimum relevance score and 50.0% minimum support similarity to prevent unwarranted claims on out-of-domain queries.

### Tier D: Team-Defined Protocols (Experimental Heuristics)
1. **Scan Quality Tiers (Tiers 1, 2, and 3)**: These are heuristic categories defined by our research team to partition degradation states for controlled comparative testing. They do **not** represent external government or ISO standards.
2. **Stratified Sampling Strata (Strata A–E)**: A team-defined heuristic allocating target proportions (Front Matter, Dense Prose, Complex Legislative, Tabular, Degraded) to prevent sampling bias across large multi-volume corpora.

### Tier E: Unresolved Research Questions (Empirical Gaps)
1. **Devanagari OCR Accuracy on Historical Paper**: It is currently **UNKNOWN** whether standard Tesseract `mar`/`hin` models achieve acceptable CER ($< 5.0\%$) on 1920s–1950s Marathi/Hindi press prints without fine-tuning.
2. **Binarization Efficacy on Aged Paper**: It is currently **UNPROVEN** whether OpenCV adaptive thresholding or CLAHE improves or harms OCR accuracy on foxed archival paper compared to raw 24-bit RGB scans.
3. **Dense Semantic vs. N-Gram Lexical Superiority**: It is currently **UNKNOWN** whether multilingual dense embeddings (BGE-M3) outperform character n-gram fuzzy matching on OCR-corrupted archival texts.

---

## 3. Strict Prohibitions

1. **No Fabricated Benchmarks**: Never record a simulated 0.0% CER or fabricated retrieval score as if it were measured on real hardware.
2. **No Unsubstantiated Novelty**: Never claim a feature is "the world's first AI algorithm" when it combines established prior art (OCR, BM25, BGE-M3, RAG).
3. **No False Perfection**: Never describe the research prototype as "100% accurate" or "hallucination-free."
4. **No Premature Gate Unlocking**: Never unlock Phase E2 or Phase E3 until Phase E1 has produced verified empirical results on authentic archival scans.
