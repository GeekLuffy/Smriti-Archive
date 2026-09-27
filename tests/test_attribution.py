"""
Tests for Phase E3 Evidence-Grounded Attribution Pipeline and Evaluator.
"""

import pytest

from sih_archive.attribution.evaluator import AttributionEvaluator
from sih_archive.attribution.pipeline import EvidenceGroundedAnswerPipeline, compute_enclosing_bbox
from sih_archive.attribution.schemas import AttributedClaim, GroundedAnswer, SourceCitation
from sih_archive.retrieval.bm25 import BM25RetrievalEngine
from sih_archive.schemas.ocr import OCROutput, ProcessingMetadata, TokenRegion


@pytest.fixture
def corpus_docs():
    doc1 = OCROutput(
        document_id="caste_in_india",
        page_id="caste_in_india_p0001",
        language="eng",
        script="Latn",
        engine="mock",
        engine_version="1.0.0",
        image_path="data/processed/pages/caste_in_india_p0001.png",
        processing=ProcessingMetadata(dpi=300, filters=["raw"], duration_ms=5.0),
        text="The population of the Punjab, Bengal and Madras may differ physically, but culturally they have a fundamental unity.",
        regions=[
            TokenRegion(region_id="t1", type="word", text="The", bbox=[100, 200, 30, 20], confidence=99.0),
            TokenRegion(region_id="t2", type="word", text="population", bbox=[135, 200, 80, 20], confidence=98.0),
            TokenRegion(region_id="t3", type="word", text="Punjab", bbox=[220, 200, 60, 20], confidence=98.0),
            TokenRegion(region_id="t4", type="word", text="Bengal", bbox=[285, 200, 60, 20], confidence=98.0),
            TokenRegion(region_id="t5", type="word", text="fundamental", bbox=[350, 200, 90, 20], confidence=97.0),
            TokenRegion(region_id="t6", type="word", text="unity", bbox=[445, 200, 45, 20], confidence=99.0),
        ],
    )
    return [doc1]


def test_compute_enclosing_bbox():
    r1 = TokenRegion(region_id="r1", type="word", text="A", bbox=[10, 20, 30, 40], confidence=90.0)
    r2 = TokenRegion(region_id="r2", type="word", text="B", bbox=[50, 10, 20, 30], confidence=90.0)
    bbox = compute_enclosing_bbox([r1, r2])
    # min_x=10, min_y=10, max_x=70 (50+20), max_y=60 (20+40) -> w=60, h=50
    assert bbox == [10, 10, 60, 50]
    assert compute_enclosing_bbox([]) is None


def test_grounded_answer_pipeline_success(corpus_docs):
    engine = BM25RetrievalEngine()
    pipeline = EvidenceGroundedAnswerPipeline(
        retrieval_engine=engine,
        min_relevance_score=0.01,
        min_support_similarity=50.0,
    )
    pipeline.register_documents(corpus_docs)

    answer = pipeline.answer_question("Do Punjab and Bengal share a fundamental cultural unity?")
    assert not answer.is_refusal
    assert len(answer.claims) == 1
    claim = answer.claims[0]
    assert claim.is_supported
    assert claim.citation is not None
    assert claim.citation.document_id == "caste_in_india"
    assert claim.citation.page_id == "caste_in_india_p0001"
    assert claim.citation.bbox is not None
    assert "fundamental unity" in claim.citation.quote_span


def test_grounded_answer_pipeline_refusal(corpus_docs):
    engine = BM25RetrievalEngine()
    pipeline = EvidenceGroundedAnswerPipeline(retrieval_engine=engine)
    pipeline.register_documents(corpus_docs)

    # Asking about completely unrelated quantum physics not in historical archive
    answer = pipeline.answer_question("What is the quantum mechanical spin of an electron in superconducting state?")
    assert answer.is_refusal
    assert "REFUSAL" in answer.answer_text
    assert answer.refusal_reason is not None
    assert len(answer.claims) == 0


def test_attribution_evaluator(corpus_docs):
    evaluator = AttributionEvaluator()
    citation = SourceCitation(
        document_id="caste_in_india",
        page_id="caste_in_india_p0001",
        quote_span="culturally they have a fundamental unity",
        bbox=[100, 200, 390, 20],
        confidence=0.95,
    )
    claim = AttributedClaim(
        claim_text="The cultural unity is fundamental.",
        citation=citation,
        is_supported=True,
    )
    answer = GroundedAnswer(
        question="What is the cultural unity?",
        answer_text="It is fundamental.",
        claims=[claim],
        is_refusal=False,
    )

    ref = [{
        "expected_page_id": "caste_in_india_p0001",
        "expected_span": "culturally they have a fundamental unity",
        "target_bbox": [100, 200, 390, 20],
    }]

    metrics = evaluator.evaluate_batch([answer], ref)
    assert metrics.total_questions == 1
    assert metrics.claim_support_rate == 1.0
    assert metrics.source_page_accuracy == 1.0
    assert metrics.mean_bbox_iou == 1.0
    assert metrics.unsupported_answer_rate == 0.0
