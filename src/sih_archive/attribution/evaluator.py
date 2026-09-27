"""
Attribution Evaluator for Phase E3 Benchmarks.
"""

from typing import Dict, List, Optional
from sih_archive.attribution.schemas import AttributionMetrics, GroundedAnswer
from sih_archive.evaluation.iou import compute_iou


class AttributionEvaluator:
    """
    Evaluates evidence-grounded answers against verified reference facts and target regions.
    """

    def evaluate_batch(
        self,
        answers: List[GroundedAnswer],
        reference_data: List[Dict],
    ) -> AttributionMetrics:
        """
        reference_data format per question:
        {
            "expected_page_id": "doc_p0001",
            "expected_span": "exact quote...",
            "target_bbox": [x, y, w, h],
        }
        """
        if not answers or len(answers) != len(reference_data):
            return AttributionMetrics(
                total_questions=len(answers),
                claim_support_rate=0.0,
                span_precision=0.0,
                mean_bbox_iou=0.0,
                broken_citation_rate=0.0,
                source_page_accuracy=0.0,
                unsupported_answer_rate=0.0,
            )

        supported_claims = 0
        total_claims = 0
        correct_pages = 0
        broken_citations = 0
        unsupported_answers = 0
        ious: List[float] = []
        span_precisions: List[float] = []

        for ans, ref in zip(answers, reference_data):
            if ans.is_refusal:
                # If ground truth was unanswerable, refusal is correct
                if ref.get("expected_page_id") is None:
                    correct_pages += 1
                continue

            if not ans.claims:
                unsupported_answers += 1
                continue

            has_unsupported = False
            for c in ans.claims:
                total_claims += 1
                if c.is_supported and c.citation:
                    supported_claims += 1
                    # Verify page
                    if c.citation.page_id == ref.get("expected_page_id"):
                        correct_pages += 1
                    else:
                        has_unsupported = True

                    # Verify BBox IoU
                    if c.citation.bbox and ref.get("target_bbox"):
                        iou = compute_iou(c.citation.bbox, ref["target_bbox"])
                        ious.append(iou)
                    elif not c.citation.bbox and not ref.get("target_bbox"):
                        ious.append(1.0)
                    else:
                        ious.append(0.0)

                    # Span token precision
                    ref_words = set(ref.get("expected_span", "").lower().split())
                    cite_words = set(c.citation.quote_span.lower().split())
                    if cite_words:
                        prec = len(cite_words & ref_words) / len(cite_words)
                        span_precisions.append(prec)
                else:
                    has_unsupported = True

            if has_unsupported:
                unsupported_answers += 1

        total_q = len(answers)
        return AttributionMetrics(
            total_questions=total_q,
            claim_support_rate=round(supported_claims / total_claims, 4) if total_claims > 0 else 0.0,
            span_precision=round(sum(span_precisions) / len(span_precisions), 4) if span_precisions else 0.0,
            mean_bbox_iou=round(sum(ious) / len(ious), 4) if ious else 0.0,
            broken_citation_rate=round(broken_citations / total_q, 4) if total_q > 0 else 0.0,
            source_page_accuracy=round(correct_pages / total_q, 4) if total_q > 0 else 0.0,
            unsupported_answer_rate=round(unsupported_answers / total_q, 4) if total_q > 0 else 0.0,
        )
