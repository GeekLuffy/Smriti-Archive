"""Phase E3 Attribution Module."""

from sih_archive.attribution.evaluator import AttributionEvaluator
from sih_archive.attribution.pipeline import EvidenceGroundedAnswerPipeline, compute_enclosing_bbox
from sih_archive.attribution.schemas import (
    AttributedClaim,
    AttributionMetrics,
    GroundedAnswer,
    SourceCitation,
)

__all__ = [
    "SourceCitation",
    "AttributedClaim",
    "GroundedAnswer",
    "AttributionMetrics",
    "compute_enclosing_bbox",
    "EvidenceGroundedAnswerPipeline",
    "AttributionEvaluator",
]
