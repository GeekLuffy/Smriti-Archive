# SIH26096 — Phase E2 Archival Retrieval Benchmark Report

- **Execution Date:** 2026-09-29 10:41:52Z
- **Gate Status:** `LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1)`
- **E1 Dependency Status:** `BLOCKED_ON_HOST_OCR_BINARY`
- **Indexed Pages:** 20 (Target: 100–200 pages)
- **Judged Queries:** 10 (Target: 50 queries)

## Scientific Gating Notice

> [!IMPORTANT]
> **Phase E2 is strictly gated on Phase E1.** Evaluating retrieval on synthetic text yields
> artificial 100% recall figures that fail to simulate historical OCR degradation.
> The benchmark below represents an implementation preview only.

## Comparative Engine Results (Preview)

| Engine | Recall@10 | nDCG@10 | MRR | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **bm25** | 0.3000 | 0.3000 | 0.2167 | 0.12 ms |
| **char_3gram_fuzzy** | 0.4500 | 0.4555 | 0.2792 | 1.44 ms |
| **dense_bge-m3** | 0.7500 | 0.6612 | 0.4897 | 0.05 ms |
| **hybrid_bm25_dense_bge-m3** | 1.0000 | 0.6029 | 0.4650 | 0.29 ms |

### Qualitative Assessment
- **No Universal Winner:** Strategy selection must be data-driven based on the document condition.
- **BM25:** High precision on uncorrupted titles, acts, and proper nouns.
- **Character 3-Gram:** Resilient to broken characters, ink bleed, and scanning artifacts.
- **Dense Semantic:** Captures conceptual relationships when exact keywords differ.
- **Hybrid (RRF):** Optimal balance for general archival discovery.
