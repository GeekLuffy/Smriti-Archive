"""
Tests for Phase E2 Retrieval Engines and IR Metrics.
"""

import pytest

from sih_archive.retrieval.base import SearchResult
from sih_archive.retrieval.bm25 import BM25RetrievalEngine
from sih_archive.retrieval.dense import DenseRetrievalEngine, MockEmbeddingModel
from sih_archive.retrieval.hybrid import HybridRetrievalEngine
from sih_archive.retrieval.metrics import (
    compute_mrr,
    compute_ndcg_at_k,
    compute_recall_at_k,
)
from sih_archive.retrieval.ngram import CharacterNGramRetrievalEngine
from sih_archive.schemas.ocr import OCROutput, ProcessingMetadata, TokenRegion


@pytest.fixture
def sample_ocr_docs():
    """Generates synthetic OCR outputs for testing retrieval."""
    doc1 = OCROutput(
        document_id="doc_ambedkar",
        page_id="doc_ambedkar_p0001",
        language="eng",
        script="Latn",
        engine="mock",
        engine_version="1.0.0",
        image_path="data/processed/pages/doc_ambedkar_p0001.png",
        processing=ProcessingMetadata(dpi=300, filters=["raw"], duration_ms=10.0),
        text="Castes in India: Their Mechanism, Genesis and Development by Dr. B.R. Ambedkar.",
        regions=[
            TokenRegion(region_id="r1", type="word", text="Castes", bbox=[10, 10, 50, 20], confidence=98.0),
            TokenRegion(region_id="r2", type="word", text="India", bbox=[65, 10, 40, 20], confidence=99.0),
            TokenRegion(region_id="r3", type="word", text="Mechanism", bbox=[110, 10, 70, 20], confidence=95.0),
            TokenRegion(region_id="r4", type="word", text="Genesis", bbox=[185, 10, 60, 20], confidence=97.0),
            TokenRegion(region_id="r5", type="word", text="Ambedkar", bbox=[250, 10, 80, 20], confidence=99.0),
        ],
    )

    doc2 = OCROutput(
        document_id="doc_ambedkar",
        page_id="doc_ambedkar_p0002",
        language="eng",
        script="Latn",
        engine="mock",
        engine_version="1.0.0",
        image_path="data/processed/pages/doc_ambedkar_p0002.png",
        processing=ProcessingMetadata(dpi=300, filters=["raw"], duration_ms=10.0),
        text="Annihilation of Caste with a reply to Mahatma Gandhi regarding social reform and political rights.",
        regions=[
            TokenRegion(region_id="r6", type="word", text="Annihilation", bbox=[10, 10, 90, 20], confidence=96.0),
            TokenRegion(region_id="r7", type="word", text="Caste", bbox=[105, 10, 45, 20], confidence=98.0),
            TokenRegion(region_id="r8", type="word", text="Gandhi", bbox=[155, 10, 50, 20], confidence=94.0),
        ],
    )

    doc3 = OCROutput(
        document_id="doc_ambedkar",
        page_id="doc_ambedkar_p0003",
        language="eng",
        script="Latn",
        engine="mock",
        engine_version="1.0.0",
        image_path="data/processed/pages/doc_ambedkar_p0003.png",
        processing=ProcessingMetadata(dpi=300, filters=["raw"], duration_ms=10.0),
        text="Constituent Assembly Debates: Fundamental rights, Directive Principles, and constitutional morality.",
        regions=[
            TokenRegion(region_id="r9", type="word", text="Constituent", bbox=[10, 10, 80, 20], confidence=99.0),
            TokenRegion(region_id="r10", type="word", text="Assembly", bbox=[95, 10, 65, 20], confidence=99.0),
        ],
    )

    return [doc1, doc2, doc3]


def test_bm25_retrieval(sample_ocr_docs):
    engine = BM25RetrievalEngine(k1=1.5, b=0.75)
    idx_res = engine.index_documents(sample_ocr_docs)
    assert idx_res.indexed_pages_count == 3
    assert idx_res.total_tokens_count > 0

    results = engine.search("Genesis Mechanism", top_k=2)
    assert len(results) > 0
    assert results[0].page_id == "doc_ambedkar_p0001"
    assert results[0].score > 0
    # Verified token bounding boxes preserved
    assert len(results[0].matched_regions) >= 2


def test_ngram_fuzzy_retrieval_with_ocr_corruption(sample_ocr_docs):
    engine = CharacterNGramRetrievalEngine(n=3, fuzzy_threshold=70.0)
    engine.index_documents(sample_ocr_docs)

    # Simulating OCR character corruption: "Arnbedkar" instead of "Ambedkar", "Gencsis" instead of "Genesis"
    results = engine.search("Arnbedkar Gencsis", top_k=2)
    assert len(results) > 0
    assert results[0].page_id == "doc_ambedkar_p0001"
    assert results[0].score > 0


def test_dense_retrieval_mock(sample_ocr_docs):
    mock_embed = MockEmbeddingModel(dim=32)
    engine = DenseRetrievalEngine(embedding_model=mock_embed)
    idx_res = engine.index_documents(sample_ocr_docs)
    assert idx_res.indexed_pages_count == 3

    results = engine.search("Constituent Assembly", top_k=3)
    assert len(results) == 3
    assert results[0].score <= 1.0


def test_hybrid_retrieval_rrf(sample_ocr_docs):
    bm25 = BM25RetrievalEngine()
    dense = DenseRetrievalEngine(embedding_model=MockEmbeddingModel(dim=16))
    hybrid = HybridRetrievalEngine(lexical_engine=bm25, dense_engine=dense, rrf_k=60)

    hybrid.index_documents(sample_ocr_docs)
    results = hybrid.search("Annihilation Gandhi", top_k=2)
    assert len(results) > 0
    assert any(r.page_id == "doc_ambedkar_p0002" for r in results)
    assert results[0].metadata["engine"].startswith("hybrid_")


def test_ir_metrics_calculations():
    retrieved = ["p0001", "p0002", "p0003", "p0004"]
    relevant = {"p0001", "p0003"}

    # Recall@2: only p0001 is in top 2 -> 1/2 = 0.5
    assert compute_recall_at_k(retrieved, relevant, k=2) == 0.5
    # Recall@4: both are in top 4 -> 2/2 = 1.0
    assert compute_recall_at_k(retrieved, relevant, k=4) == 1.0

    # MRR: first relevant is at rank 1 -> 1.0 / 1 = 1.0
    assert compute_mrr(retrieved, relevant) == 1.0
    # MRR when first relevant is at rank 2
    assert compute_mrr(["p0005", "p0001"], relevant) == 0.5

    # nDCG@K with graded relevance
    graded_rel = {"p0001": 3.0, "p0003": 2.0}
    ndcg = compute_ndcg_at_k(retrieved, graded_rel, k=4)
    assert 0.0 < ndcg <= 1.0
