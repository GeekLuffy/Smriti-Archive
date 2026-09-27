"""
Okapi BM25 Lexical Retrieval Engine for Phase E2 Archival Search.
"""

from collections import Counter
import math
import re
import time
from typing import Any, Dict, List, Optional

from sih_archive.retrieval.base import IndexingResult, RetrievalEngine, SearchResult
from sih_archive.schemas.ocr import OCROutput, TokenRegion


def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric tokens."""
    return re.findall(r"\b\w+\b", text.lower())


class BM25RetrievalEngine(RetrievalEngine):
    """
    Okapi BM25 implementation designed specifically for OCR outputs.
    Preserves token-level bounding boxes for matched query terms.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: List[OCROutput] = []
        self.doc_len: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = Counter()
        self.doc_tokens: List[List[str]] = []
        self.total_docs: int = 0

    @property
    def name(self) -> str:
        return "bm25"

    def index_documents(self, documents: List[OCROutput]) -> IndexingResult:
        t0 = time.perf_counter()
        self.docs = list(documents)
        self.total_docs = len(self.docs)
        self.doc_tokens = []
        self.doc_len = []
        self.doc_freqs = Counter()

        total_tokens = 0
        for doc in self.docs:
            tokens = tokenize(doc.text)
            self.doc_tokens.append(tokens)
            l = len(tokens)
            self.doc_len.append(l)
            total_tokens += l
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] += 1

        self.avg_doc_len = (total_tokens / self.total_docs) if self.total_docs > 0 else 0.0
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return IndexingResult(
            indexed_pages_count=self.total_docs,
            total_tokens_count=total_tokens,
            duration_ms=round(elapsed_ms, 2),
            engine_name=self.name,
        )

    def _idf(self, term: str) -> float:
        """Computes Robertson-Spärck Jones IDF with smoothing."""
        df = self.doc_freqs.get(term, 0)
        # Using standard Lucene / Okapi BM25 smoothed IDF
        return math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        if not self.docs or self.total_docs == 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.total_docs

        for q in query_tokens:
            idf = self._idf(q)
            if idf <= 0.0:
                continue

            for i in range(self.total_docs):
                tokens = self.doc_tokens[i]
                tf = tokens.count(q)
                if tf == 0:
                    continue

                denom = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_len[i] / self.avg_doc_len if self.avg_doc_len > 0 else 1.0))
                score = idf * (tf * (self.k1 + 1.0)) / denom
                scores[i] += score

        ranked_indices = sorted(
            [i for i in range(self.total_docs) if scores[i] > 0.0],
            key=lambda idx: scores[idx],
            reverse=True,
        )[:top_k]

        results = []
        for idx in ranked_indices:
            doc = self.docs[idx]
            # Match token regions for query terms to enable visual grounding
            matched = [
                r for r in doc.regions
                if any(q == r.text.lower().strip(".,:;!?\"'") for q in query_tokens)
            ]
            results.append(
                SearchResult(
                    document_id=doc.document_id,
                    page_id=doc.page_id,
                    score=round(scores[idx], 4),
                    text=doc.text.strip(),
                    matched_regions=matched,
                    metadata={"engine": self.name, "rank": len(results) + 1},
                )
            )

        return results
