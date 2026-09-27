"""
Character N-Gram & Fuzzy Lexical Retrieval Engine for OCR-Corrupted Text.
"""

from collections import Counter
import time
from typing import Any, Dict, List, Optional, Set
import rapidfuzz.fuzz as fuzz

from sih_archive.retrieval.base import IndexingResult, RetrievalEngine, SearchResult
from sih_archive.schemas.ocr import OCROutput, TokenRegion


def get_char_ngrams(text: str, n: int = 3) -> Set[str]:
    """Generates a set of character n-grams from normalized text."""
    clean = " ".join(text.lower().split())
    if len(clean) < n:
        return {clean} if clean else set()
    return {clean[i : i + n] for i in range(len(clean) - n + 1)}


class CharacterNGramRetrievalEngine(RetrievalEngine):
    """
    Retrieval engine using character n-grams (default 3-grams) and RapidFuzz token matching.
    Robust to character substitutions, OCR deletions, and aged scan artifacts.
    """

    def __init__(self, n: int = 3, fuzzy_threshold: float = 75.0):
        self.n = n
        self.fuzzy_threshold = fuzzy_threshold
        self.docs: List[OCROutput] = []
        self.doc_ngrams: List[Set[str]] = []

    @property
    def name(self) -> str:
        return f"char_{self.n}gram_fuzzy"

    def index_documents(self, documents: List[OCROutput]) -> IndexingResult:
        t0 = time.perf_counter()
        self.docs = list(documents)
        self.doc_ngrams = []
        total_tokens = 0

        for doc in self.docs:
            ngrams = get_char_ngrams(doc.text, n=self.n)
            self.doc_ngrams.append(ngrams)
            total_tokens += len(doc.regions)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return IndexingResult(
            indexed_pages_count=len(self.docs),
            total_tokens_count=total_tokens,
            duration_ms=round(elapsed_ms, 2),
            engine_name=self.name,
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        if not self.docs:
            return []

        query_clean = query.strip().lower()
        query_ngrams = get_char_ngrams(query_clean, n=self.n)
        if not query_ngrams:
            return []

        scores: List[float] = []

        for i, doc in enumerate(self.docs):
            doc_ng = self.doc_ngrams[i]
            if not doc_ng:
                scores.append(0.0)
                continue

            # Jaccard overlap of character n-grams
            intersection = len(query_ngrams & doc_ng)
            union = len(query_ngrams | doc_ng)
            jaccard = (intersection / union) if union > 0 else 0.0

            # Substring fuzzy partial ratio
            partial = fuzz.partial_ratio(query_clean, doc.text.lower()) / 100.0

            # Combined score weighting n-gram overlap and fuzzy string alignment
            combined = 0.5 * jaccard + 0.5 * partial
            scores.append(combined)

        ranked = sorted(
            [i for i in range(len(self.docs)) if scores[i] > 0.0],
            key=lambda idx: scores[idx],
            reverse=True,
        )[:top_k]

        results = []
        q_words = query_clean.split()
        for idx in ranked:
            doc = self.docs[idx]
            # Match tokens fuzzily
            matched = [
                r for r in doc.regions
                if any(fuzz.ratio(w, r.text.lower().strip(".,:;!?\"'")) >= self.fuzzy_threshold for w in q_words)
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
