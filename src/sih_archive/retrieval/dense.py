"""
Dense Vector Retrieval Interface & BGE-M3 Adapter Abstraction.
"""

from abc import ABC, abstractmethod
import time
from typing import Any, Callable, Dict, List, Optional
import numpy as np

from sih_archive.retrieval.base import IndexingResult, RetrievalEngine, SearchResult
from sih_archive.schemas.ocr import OCROutput


class EmbeddingModel(ABC):
    """Abstract embedding model interface (e.g. BGE-M3)."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Returns 2D numpy array of shape (N, dim) with normalized embeddings."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass


class MockEmbeddingModel(EmbeddingModel):
    """Deterministic hash-based mock embedding model for CI and offline testing."""

    def __init__(self, dim: int = 64):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            # Deterministic pseudo-vector seeded by text hash
            h = abs(hash(text))
            rng = np.random.default_rng(h % (2**32))
            v = rng.standard_normal(self._dim)
            norm = np.linalg.norm(v)
            if norm > 0:
                v = v / norm
            vectors.append(v)
        return np.array(vectors, dtype=np.float32)


class DenseRetrievalEngine(RetrievalEngine):
    """
    Dense vector search engine utilizing embeddings and cosine similarity.
    Designed for BGE-M3 dense multilingual representations.
    """

    def __init__(self, embedding_model: Optional[EmbeddingModel] = None, model_name: str = "bge-m3"):
        self.embedding_model = embedding_model or MockEmbeddingModel()
        self.model_name = model_name
        self.docs: List[OCROutput] = []
        self.embeddings: Optional[np.ndarray] = None

    @property
    def name(self) -> str:
        return f"dense_{self.model_name}"

    def index_documents(self, documents: List[OCROutput]) -> IndexingResult:
        t0 = time.perf_counter()
        self.docs = list(documents)
        texts = [doc.text.strip() for doc in self.docs]

        if texts:
            self.embeddings = self.embedding_model.embed_texts(texts)
        else:
            self.embeddings = np.empty((0, self.embedding_model.dimension), dtype=np.float32)

        total_tokens = sum(len(doc.regions) for doc in self.docs)
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
        if not self.docs or self.embeddings is None or len(self.embeddings) == 0:
            return []

        q_vec = self.embedding_model.embed_texts([query])[0]
        # Cosine similarity (both embeddings normalized)
        scores = np.dot(self.embeddings, q_vec)

        ranked = np.argsort(scores)[::-1][:top_k]
        results = []
        for rank_idx, idx in enumerate(ranked):
            doc = self.docs[idx]
            score_val = float(scores[idx])
            results.append(
                SearchResult(
                    document_id=doc.document_id,
                    page_id=doc.page_id,
                    score=round(score_val, 4),
                    text=doc.text.strip(),
                    matched_regions=[],
                    metadata={"engine": self.name, "rank": rank_idx + 1},
                )
            )

        return results
