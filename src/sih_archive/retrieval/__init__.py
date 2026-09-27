"""Phase E2 Retrieval Module."""

from sih_archive.retrieval.base import IndexingResult, RetrievalEngine, SearchResult
from sih_archive.retrieval.bm25 import BM25RetrievalEngine
from sih_archive.retrieval.dense import DenseRetrievalEngine, EmbeddingModel, MockEmbeddingModel
from sih_archive.retrieval.hybrid import HybridRetrievalEngine
from sih_archive.retrieval.metrics import (
    RetrievalMetrics,
    compute_mrr,
    compute_ndcg_at_k,
    compute_recall_at_k,
)
from sih_archive.retrieval.ngram import CharacterNGramRetrievalEngine

__all__ = [
    "SearchResult",
    "IndexingResult",
    "RetrievalEngine",
    "BM25RetrievalEngine",
    "CharacterNGramRetrievalEngine",
    "EmbeddingModel",
    "MockEmbeddingModel",
    "DenseRetrievalEngine",
    "HybridRetrievalEngine",
    "RetrievalMetrics",
    "compute_recall_at_k",
    "compute_mrr",
    "compute_ndcg_at_k",
]
