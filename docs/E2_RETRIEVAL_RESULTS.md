# Phase E2: Archival Retrieval Benchmark & Strategy Evaluation

**Status**: **STRICTLY LOCKED (Awaiting Empirical Completion of Phase E1)**  
**Benchmark Date**: 2026-09-27  
**Module Location**: `src/sih_archive/retrieval/`  
**Test Suite**: `tests/test_retrieval.py` (5 passing tests)  

---

## 1. Phase Gate Status

```
   [ Phase E0: Corpus & Rights Protocol ]  ──► PASS
                     │
                     ▼
   [ Phase E1: Real Archival OCR Benchmark ] ──► BLOCKED / INCOMPLETE (Host OCR binary pending)
                     │
                     ▼
   [ Phase E2: Archival Retrieval Benchmark ] ──► STRICTLY LOCKED
```

> [!IMPORTANT]
> **GATING NOTICE**: In adherence to SIH26096 research integrity principles, **Phase E2 remains locked**. Evaluating retrieval on synthetic text or unverified OCR produces fabricated ranking scores. The software interfaces, schemas, and test harnesses for Phase E2 have been fully designed and validated offline so that execution can occur immediately once Phase E1 satisfies its empirical gate.

---

## 2. Benchmark Retrieval Architectures Implemented

The framework implements four distinct retrieval strategies behind a common `RetrievalEngine` interface:

1. **BM25 Lexical Retrieval (`BM25RetrievalEngine`)**:
   - Implements Okapi BM25 ranking ($k_1 = 1.5, b = 0.75$) with Robertson-Spärck Jones smoothed IDF.
   - Extracts matched query token regions directly from `OCROutput.regions` to provide immediate coordinate bounding boxes for downstream visual highlighting.
2. **Character N-Gram & Fuzzy Lexical Retrieval (`CharacterNGramRetrievalEngine`)**:
   - Computes character 3-gram and 4-gram Jaccard overlap combined with RapidFuzz partial substring alignment.
   - Designed specifically to withstand historical OCR corruption (e.g., misrecognizing *"Ambedkar"* as *"Arnbedkar"* or *"genesis"* as *"gcncsis"*).
3. **Dense Vector Retrieval (`DenseRetrievalEngine`)**:
   - Dense semantic vector search using normalized cosine similarity embeddings.
   - Standardized around the **BGE-M3** multilingual embedding architecture (supporting English, Hindi, and Marathi). Includes an offline deterministic mock embedding provider for CI testing.
4. **Hybrid Retrieval with Reciprocal Rank Fusion (`HybridRetrievalEngine`)**:
   - Combines lexical candidate sets (BM25 or N-Gram) and dense candidate sets using Reciprocal Rank Fusion:
     $$\text{RRF\_Score}(d) = \sum_{m \in M} \frac{1}{60 + \text{rank}_m(d)}$$
   - Preserves token bounding boxes from lexical matches while benefiting from semantic dense coverage.

---

## 3. Graded Evaluation Query Protocol (Planned Experiment)

Once Phase E1 is unlocked, the retrieval benchmark will evaluate a standardized query set of 50 historical queries across four categories:

| Query Category | Example Query | Target Evaluation Challenge |
| :--- | :--- | :--- |
| **Named Entities** | *"Castes in India Vasant Moon"* | Precise keyword indexing; capitalization handling. |
| **Historical Phrases** | *"social reform and political rights"* | Phrase proximity; term frequency weighting. |
| **Multilingual / Indic Terms** | *"bahishkrit hitakarini sabha"* | Cross-lingual transliteration; romanized vs. Devanagari matching. |
| **OCR-Corrupted Queries** | *"Arnbedkar Gencsis Mechanism"* | Resiliency of character n-gram fuzzy matching vs. brittle exact lexical search. |
| **Broad Semantic Inquiries** | *"constitutional morality and fundamental rights"* | Dense semantic vector generalization beyond keyword overlap. |

### Evaluation Metrics
- **Recall@10**: Proportion of relevant archival pages retrieved within the top 10 candidates.
- **nDCG@10**: Normalized Discounted Cumulative Gain accounting for graded relevance (0 = irrelevant, 1 = related, 2 = highly relevant, 3 = primary source).
- **MRR (Mean Reciprocal Rank)**: Speed of surfacing the first relevant historical document.
- **Query Latency (ms)**: Search latency measured across index sizes.

---

## 4. Verification & Readiness

All retrieval engines and IR metrics are verified in `tests/test_retrieval.py`:
- `test_bm25_retrieval`: PASSED
- `test_ngram_fuzzy_retrieval_with_ocr_corruption`: PASSED
- `test_dense_retrieval_mock`: PASSED
- `test_hybrid_retrieval_rrf`: PASSED
- `test_ir_metrics_calculations`: PASSED
