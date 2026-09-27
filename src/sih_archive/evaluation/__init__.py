"""Evaluation subpackage for OCR accuracy benchmarking and error metrics."""

from sih_archive.evaluation.cer_wer import compute_cer, compute_wer, normalize_text
from sih_archive.evaluation.iou import compute_iou, match_bounding_boxes
from sih_archive.evaluation.reading_order import (
    KendallTauReadingOrderEvaluator,
    ReadingOrderEvaluator,
)

__all__ = [
    "compute_cer",
    "compute_wer",
    "normalize_text",
    "compute_iou",
    "match_bounding_boxes",
    "ReadingOrderEvaluator",
    "KendallTauReadingOrderEvaluator",
]
