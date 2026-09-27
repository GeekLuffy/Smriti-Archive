"""
Evidence-Grounded Answer Pipeline with Sentence-Level Attribution and Refusal Gate.
"""

import re
from typing import Dict, List, Optional
import rapidfuzz.fuzz as fuzz

from sih_archive.attribution.schemas import AttributedClaim, GroundedAnswer, SourceCitation
from sih_archive.retrieval.base import RetrievalEngine
from sih_archive.schemas.ocr import OCROutput, TokenRegion


def compute_enclosing_bbox(regions: List[TokenRegion]) -> Optional[List[int]]:
    """Calculates the bounding box [x, y, w, h] enclosing a sequence of token regions."""
    if not regions:
        return None
    min_x = min(r.bbox[0] for r in regions)
    min_y = min(r.bbox[1] for r in regions)
    max_x = max(r.bbox[0] + r.bbox[2] for r in regions)
    max_y = max(r.bbox[1] + r.bbox[3] for r in regions)
    return [min_x, min_y, max_x - min_x, max_y - min_y]


class EvidenceGroundedAnswerPipeline:
    """
    Synthesizes research answers from retrieved archival OCR pages.
    Enforces strict evidence grounding: every claim must cite a specific page,
    text span, and bounding box. Refuses when retrieved evidence is insufficient.
    """

    def __init__(
        self,
        retrieval_engine: RetrievalEngine,
        min_relevance_score: float = 0.1,
        min_support_similarity: float = 70.0,
    ):
        self.retrieval_engine = retrieval_engine
        self.min_relevance_score = min_relevance_score
        self.min_support_similarity = min_support_similarity
        self.indexed_docs_map: Dict[str, OCROutput] = {}

    def register_documents(self, documents: List[OCROutput]) -> None:
        """Stores reference documents for coordinate and token lookup."""
        self.indexed_docs_map = {doc.page_id: doc for doc in documents}
        self.retrieval_engine.index_documents(documents)

    def answer_question(self, question: str, top_k: int = 3) -> GroundedAnswer:
        search_results = self.retrieval_engine.search(question, top_k=top_k)
        retrieved_page_ids = [res.page_id for res in search_results]

        # Refusal Gate 1: No results or score below threshold
        if not search_results or search_results[0].score < self.min_relevance_score:
            return GroundedAnswer(
                question=question,
                answer_text="REFUSAL: Insufficient archival evidence retrieved to verify claim.",
                claims=[],
                is_refusal=True,
                refusal_reason="No archival passages met the minimum relevance threshold.",
                retrieved_page_ids=retrieved_page_ids,
            )

        best_hit = search_results[0]
        doc = self.indexed_docs_map.get(best_hit.page_id)
        if not doc:
            return GroundedAnswer(
                question=question,
                answer_text="REFUSAL: Retrieved source record could not be dereferenced.",
                claims=[],
                is_refusal=True,
                refusal_reason=f"Page {best_hit.page_id} missing from indexed corpus.",
                retrieved_page_ids=retrieved_page_ids,
            )

        # Segment retrieved text into sentences to locate grounded passage
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", doc.text) if s.strip()]
        best_sentence = None
        best_sim = 0.0

        for s in sentences:
            sim = fuzz.token_set_ratio(question, s)
            if sim > best_sim:
                best_sim = sim
                best_sentence = s

        # Refusal Gate 2: Evidence sentence does not match question topic sufficiently
        if not best_sentence or best_sim < self.min_support_similarity:
            return GroundedAnswer(
                question=question,
                answer_text="REFUSAL: Retrieved documents do not contain direct evidence addressing this specific inquiry.",
                claims=[],
                is_refusal=True,
                refusal_reason=f"Top candidate match similarity ({best_sim:.1f}%) below minimum support threshold ({self.min_support_similarity}%).",
                retrieved_page_ids=retrieved_page_ids,
            )

        # Locate corresponding word token bounding boxes in the matched sentence
        words_in_sentence = set(re.findall(r"\b\w+\b", best_sentence.lower()))
        matched_tokens = [
            r for r in doc.regions
            if r.text.lower().strip(".,:;!?\"'") in words_in_sentence
        ]
        bbox = compute_enclosing_bbox(matched_tokens)

        citation = SourceCitation(
            document_id=doc.document_id,
            page_id=doc.page_id,
            quote_span=best_sentence,
            bbox=bbox,
            confidence=round(best_sim / 100.0, 3),
        )

        claim = AttributedClaim(
            claim_text=f"According to {doc.document_id} (Page {doc.page_id}), {best_sentence}",
            citation=citation,
            is_supported=True,
        )

        return GroundedAnswer(
            question=question,
            answer_text=f"Evidence indicates: \"{best_sentence}\" [Source: {doc.document_id}, Page: {doc.page_id}]",
            claims=[claim],
            is_refusal=False,
            refusal_reason=None,
            retrieved_page_ids=retrieved_page_ids,
        )
