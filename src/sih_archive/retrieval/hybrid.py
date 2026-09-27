"""
Hybrid Retrieval Engine Combining Lexical (BM25/N-Gram) and Dense Vector Search.
"""

from collections import defaultdict
import time
from typing import Any, Dict, List, Optional

from sih_archive.retrieval.base import IndexingResult, RetrievalEngine, SearchResult
from sih_archive.schemas.ocr import OCROutput


class HybridRetrievalEngine(RetrievalEngine):
    """
    Hybrid Retrieval combining Lexical (e.g. BM25 or Char N-Gram) and Dense representations.
    Merges candidate lists using Reciprocal Rank Fusion (RRF) at k=60.
    """

    def __init__(
        self,
        lexical_engine: RetrievalEngine,
        dense_engine: RetrievalEngine,
        rrf_k: int = 60,
    ):
        self.lexical_engine = lexical_engine
        self.dense_engine = dense_engine
        self.rrf_k = rrf_k
        self.docs: List[OCROutput] = []

    @property
    def name(self) -> str:
        return f"hybrid_{self.lexical_engine.name}_{self.dense_engine.name}"

    def index_documents(self, documents: List[OCROutput]) -> IndexingResult:
        t0 = time.perf_counter()
        self.docs = list(documents)
        res_lex = self.lexical_engine.index_documents(documents)
        res_dense = self.dense_engine.index_documents(documents)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return IndexingResult(
            indexed_pages_count=len(self.docs),
            total_tokens_count=res_lex.total_tokens_count,
            duration_ms=round(elapsed_ms, 2),
            engine_name=self.name,
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        lex_results = self.lexical_engine.search(query, top_k=top_k * 2, filters=filters)
        dense_results = self.dense_engine.search(query, top_k=top_k * 2, filters=filters)

        # Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = defaultdict(float)
        items_by_key: Dict[str, SearchResult] = {}

        for rank, res in enumerate(lex_results, start=1):
            key = f"{res.document_id}_{res.page_id}"
            rrf_scores[key] += 1.0 / (self.rrf_k + rank)
            items_by_key[key] = res

        for rank, res in enumerate(dense_results, start=1):
            key = f"{res.document_id}_{res.page_id}"
            rrf_scores[key] += 1.0 / (self.rrf_k + rank)
            if key not in items_by_key:
                items_by_key[key] = res
            else:
                # Merge metadata
                items_by_key[key].metadata["dense_rank"] = rank

        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k]

        fused_results = []
        for rank_idx, key in enumerate(sorted_keys, start=1):
            base_item = items_by_key[key]
            fused_results.append(
                SearchResult(
                    document_id=base_item.document_id,
                    page_id=base_item.page_id,
                    score=round(rrf_scores[key], 6),
                    text=base_item.text,
                    matched_regions=base_item.matched_regions,
                    metadata={
                        "engine": self.name,
                        "rank": rank_idx,
                        "rrf_score": rrf_scores[key],
                    },
                )
            )

        return fused_results
