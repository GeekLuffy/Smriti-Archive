# Phase E3: Evidence-Grounded Attribution & Citation Verification

**Status**: **STRICTLY LOCKED (Awaiting Completion of Phase E1 & Phase E2)**  
**Benchmark Date**: 2026-09-27  
**Module Location**: `src/sih_archive/attribution/`  
**Test Suite**: `tests/test_attribution.py` (4 passing tests)  

---

## 1. Phase Gate Status

```
   [ Phase E1: Real Archival OCR Benchmark ] ──► BLOCKED / INCOMPLETE
                     │
                     ▼
   [ Phase E2: Retrieval Benchmark ] ──────────► LOCKED
                     │
                     ▼
   [ Phase E3: Evidence Attribution ] ─────────► STRICTLY LOCKED
```

> [!IMPORTANT]
> **GATING NOTICE**: Phase E3 cannot produce authoritative attribution scores without real archival OCR tokens and validated retrieval indexes. The attribution pipeline, schemas, refusal mechanisms, and evaluation metrics have been implemented and tested to establish forward architectural compatibility.

---

## 2. Evidence Grounding & Citation Architecture

The SIH26096 attribution architecture enforces an unbroken, machine-verifiable chain of custody from user inquiry to original archival scan coordinates:

```
USER RESEARCH QUESTION
       │
       ▼
RETRIEVAL ENGINE (BM25 / Hybrid)
       │
       ▼
SOURCE PAGE CANDIDATE (document_id, page_id)
       │
       ▼
OCR TOKENS & REGIONS (Text, Token BBoxes, Line/Block Hierarchy)
       │
       ▼
CLAIM SYNTHESIS & REFUSAL GATE
  ├── If Evidence Sufficient ──► Grounded Claim + Quote Span + Bounding Box [x, y, w, h]
  └── If Evidence Missing   ──► Explicit Refusal Notice (No Hallucination)
       │
       ▼
VIEWER TARGET (High-resolution archival highlight overlay)
```

### 2.1 Refusal Policy: Prevention of AI Hallucinations
- **No Unsubstantiated Claims**: In accordance with research integrity rules, the system is **not** claimed to be "100% hallucination-free." Instead, it uses an algorithmic refusal gate (`min_relevance_score` and `min_support_similarity`).
- When retrieved passages fail to exhibit direct textual overlap or semantic relevance with the user inquiry, the system explicitly outputs a `REFUSAL` record documenting the reason.
- Fabricating citations or assigning coordinates to hallucinated answers is strictly prohibited.

---

## 3. Quantitative Attribution Metrics Implemented

The `AttributionEvaluator` module calculates the following metrics over benchmark question sets:

| Metric | Mathematical Definition | Significance |
| :--- | :--- | :--- |
| **Claim Support Rate** | $\frac{\text{Supported Claims}}{\text{Total Synthesized Claims}}$ | Proportion of claims verified by cited quotes. |
| **Span Precision** | $\frac{|\text{Tokens}_{\text{cited}} \cap \text{Tokens}_{\text{reference}}|}{|\text{Tokens}_{\text{cited}}|}$ | Accuracy of cited quote span boundaries. |
| **Mean BBox IoU** | $\frac{1}{N} \sum \text{IoU}(\text{BBox}_{\text{cited}}, \text{BBox}_{\text{target}})$ | Visual grounding accuracy on archival scans. |
| **Broken Citation Rate** | $\frac{\text{Citations to invalid page/doc}}{\text{Total Citations}}$ | Integrity of document and page links. |
| **Source Page Accuracy** | $\frac{\text{Answers with correct page ID}}{\text{Total Evaluated Answers}}$ | Accuracy of top retrieved source page. |
| **Unsupported Answer Rate** | $\frac{\text{Answers with }\ge 1\text{ ungrounded claim}}{\text{Total Answers}}$ | Frequency of unverified responses. |

---

## 4. Verification & Readiness

All attribution components are verified in `tests/test_attribution.py`:
- `test_compute_enclosing_bbox`: PASSED (Correct spatial coordinate aggregation)
- `test_grounded_answer_pipeline_success`: PASSED (Grounded claim with page and bounding box)
- `test_grounded_answer_pipeline_refusal`: PASSED (Explicit refusal on out-of-domain query)
- `test_attribution_evaluator`: PASSED (100% claim support and IoU calculation on verified reference)
