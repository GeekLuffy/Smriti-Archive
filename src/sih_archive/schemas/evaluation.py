"""
Pydantic v2 schemas for Ground Truth annotations and standardized OCR evaluation metrics (Requirement R5).

Enforces the explicit 'ground_truth_unavailable' protocol: when annotations are absent,
returns explicit null metrics and never fabricates 0.0 or synthetic statistics.
"""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


EvaluationStatus = Literal["evaluated", "ground_truth_unavailable", "error"]
VerificationStatus = Literal["draft", "verified", "double_keyed"]
RegionType = Literal["word", "line", "paragraph", "heading", "table", "margin_note", "block"]


class GroundTruthRegion(BaseModel):
    """Ground truth reference bounding box and text segment for page layout evaluation."""

    region_id: str = Field(..., description="Unique region identifier within the page.")
    type: RegionType = Field(default="word", description="Region classification type.")
    text: Optional[str] = Field(default=None, description="Transcribed ground truth text for this region.")
    bbox: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box coordinates [x, y, w, h] in absolute pixel space.",
    )
    reading_order_index: Optional[int] = Field(
        default=None,
        ge=0,
        description="0-based canonical reading order index.",
    )

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: List[int]) -> List[int]:
        if len(v) != 4:
            raise ValueError("Bounding box must contain exactly 4 integers: [x, y, w, h].")
        x, y, w, h = v
        if x < 0 or y < 0:
            raise ValueError(f"Origin coordinates (x={x}, y={y}) cannot be negative.")
        if w < 0 or h < 0:
            raise ValueError(f"Dimensions (w={w}, h={h}) cannot be negative.")
        return v


class GroundTruthPage(BaseModel):
    """
    Manually curated reference transcription and geometry for an archival page.
    """

    document_id: str = Field(..., description="Source document identifier.")
    page_id: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_\-]+_p\d{4}$",
        description="Page identifier formatted as '{document_id}_p{page_num:04d}'.",
    )
    reference_text: str = Field(..., description="Verbatim reference transcription.")
    language: str = Field(default="eng", description="Language code (ISO 639-3).")
    script: Optional[str] = Field(default="Latn", description="Script code (ISO 15924).")
    annotator: Optional[str] = Field(default=None, description="Identifier of human annotator or institution.")
    annotation_date: Optional[str] = Field(default=None, description="Date of annotation (YYYY-MM-DD).")
    verification_status: VerificationStatus = Field(
        default="draft",
        description="Hygiene status: 'draft', 'verified', or 'double_keyed'.",
    )
    notes: Optional[str] = Field(default=None, description="Annotation observations or degradation notes.")
    regions: Optional[List[GroundTruthRegion]] = Field(
        default=None,
        description="Optional list of layout regions with bounding boxes.",
    )

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Serializes GroundTruthPage to a JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "GroundTruthPage":
        """Loads and validates GroundTruthPage from a JSON file."""
        target = Path(file_path)
        if not target.is_file():
            raise FileNotFoundError(f"Ground truth file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)


# Alias for compatibility with survey report naming
GroundTruth = GroundTruthPage


class EditOperationBreakdown(BaseModel):
    """Detailed decomposition of Levenshtein edit distance operations."""

    substitutions: int = Field(ge=0, description="Count of replaced tokens (S).")
    deletions: int = Field(ge=0, description="Count of omitted tokens from reference (D).")
    insertions: int = Field(ge=0, description="Count of spurious tokens added in hypothesis (I).")
    reference_length: int = Field(ge=0, description="Total token length of reference string (N).")
    hypothesis_length: int = Field(ge=0, description="Total token length of hypothesis string (M).")
    total_distance: int = Field(ge=0, description="Total edit distance (S + D + I).")
    error_rate: float = Field(ge=0.0, description="Error rate = (S + D + I) / N (can exceed 1.0 on severe insertions).")


class BoundingBoxMetrics(BaseModel):
    """Geometric evaluation metrics comparing hypothesis bounding boxes to reference regions."""

    total_hypothesis_boxes: int = Field(ge=0, description="Total boxes detected by OCR hypothesis.")
    total_reference_boxes: int = Field(ge=0, description="Total boxes in ground truth reference.")
    true_positives: int = Field(ge=0, description="Matched pairs meeting the IoU threshold.")
    false_positives: int = Field(ge=0, description="Unmatched hypothesis boxes.")
    false_negatives: int = Field(ge=0, description="Unmatched reference boxes.")
    precision: float = Field(ge=0.0, le=1.0, description="Precision = TP / (TP + FP).")
    recall: float = Field(ge=0.0, le=1.0, description="Recall = TP / (TP + FN).")
    f1: float = Field(ge=0.0, le=1.0, description="F1 Score = 2*P*R / (P + R).")
    mean_iou: float = Field(ge=0.0, le=1.0, description="Mean IoU over matched pairs.")
    iou_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Matching IoU threshold tau.")
    matched_pairs_count: int = Field(ge=0, description="Number of successfully matched region pairs.")


class PageMetrics(BaseModel):
    """Evaluation result for an individual document page."""

    document_id: str = Field(..., description="Source document identifier.")
    page_id: str = Field(..., description="Page identifier.")
    engine: Optional[str] = Field(default=None, description="OCR engine evaluated ('tesseract', 'mock').")
    pipeline: Optional[str] = Field(default=None, description="Preprocessing pipeline applied ('raw', 'otsu', etc.).")
    status: EvaluationStatus = Field(
        default="evaluated",
        description="Status: 'evaluated', 'ground_truth_unavailable', or 'error'.",
    )
    message: Optional[str] = Field(default=None, description="Diagnostic notice or error description.")
    cer: Optional[float] = Field(default=None, description="Character Error Rate (null if ground truth unavailable).")
    wer: Optional[float] = Field(default=None, description="Word Error Rate (null if ground truth unavailable).")
    cer_breakdown: Optional[EditOperationBreakdown] = Field(
        default=None,
        description="CER edit operation breakdown.",
    )
    wer_breakdown: Optional[EditOperationBreakdown] = Field(
        default=None,
        description="WER edit operation breakdown.",
    )
    bbox_metrics: Optional[BoundingBoxMetrics] = Field(
        default=None,
        description="Bounding box IoU precision/recall/F1 metrics.",
    )
    reading_order_score: Optional[float] = Field(
        default=None,
        description="Reading order consistency score in [0.0, 1.0] (Kendall's Tau normalized).",
    )
    evaluation_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of evaluation.",
    )

    @classmethod
    def create_unavailable(
        cls,
        document_id: str,
        page_id: str,
        engine: Optional[str] = None,
        pipeline: Optional[str] = None,
        message: Optional[str] = None,
    ) -> "PageMetrics":
        """
        Factory adhering to R5 Ground Truth Unavailable protocol:
        never fabricates 0.0 or synthetic stats when annotations are absent.
        """
        msg = message or f"Ground truth unavailable: no reference annotation found for page {page_id}."
        return cls(
            document_id=document_id,
            page_id=page_id,
            engine=engine,
            pipeline=pipeline,
            status="ground_truth_unavailable",
            message=msg,
            cer=None,
            wer=None,
            cer_breakdown=None,
            wer_breakdown=None,
            bbox_metrics=None,
            reading_order_score=None,
        )

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Serializes PageMetrics to a JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "PageMetrics":
        """Loads PageMetrics from a JSON file."""
        target = Path(file_path)
        if not target.is_file():
            raise FileNotFoundError(f"Metrics file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)


class SummaryMetrics(BaseModel):
    """Aggregated evaluation metrics across multiple pages or entire archival documents."""

    total_pages: int = Field(default=0, ge=0, description="Total pages processed.")
    evaluated_pages: int = Field(default=0, ge=0, description="Pages with verified ground truth evaluated.")
    unavailable_pages: int = Field(default=0, ge=0, description="Pages where ground truth was unavailable.")
    error_pages: int = Field(default=0, ge=0, description="Pages where evaluation failed.")
    mean_cer: Optional[float] = Field(default=None, description="Arithmetic mean CER over evaluated pages.")
    mean_wer: Optional[float] = Field(default=None, description="Arithmetic mean WER over evaluated pages.")
    mean_precision: Optional[float] = Field(default=None, description="Mean bounding box precision.")
    mean_recall: Optional[float] = Field(default=None, description="Mean bounding box recall.")
    mean_f1: Optional[float] = Field(default=None, description="Mean bounding box F1 score.")
    mean_iou: Optional[float] = Field(default=None, description="Mean IoU of matched bounding boxes.")
    mean_reading_order_score: Optional[float] = Field(
        default=None,
        description="Mean reading order score across pages with matched boxes.",
    )
    page_metrics: List[PageMetrics] = Field(default_factory=list, description="Per-page evaluation metrics.")

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Serializes SummaryMetrics to a JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)

    def to_csv_file(self, file_path: Union[str, Path]) -> None:
        """Exports page-level metrics tabular summary to CSV."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "document_id",
            "page_id",
            "engine",
            "pipeline",
            "status",
            "cer",
            "wer",
            "cer_substitutions",
            "cer_deletions",
            "cer_insertions",
            "wer_substitutions",
            "wer_deletions",
            "wer_insertions",
            "bbox_precision",
            "bbox_recall",
            "bbox_f1",
            "mean_iou",
            "reading_order_score",
            "message",
        ]
        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for pm in self.page_metrics:
                row = [
                    pm.document_id,
                    pm.page_id,
                    pm.engine or "",
                    pm.pipeline or "",
                    pm.status,
                    f"{pm.cer:.4f}" if pm.cer is not None else "",
                    f"{pm.wer:.4f}" if pm.wer is not None else "",
                    pm.cer_breakdown.substitutions if pm.cer_breakdown else "",
                    pm.cer_breakdown.deletions if pm.cer_breakdown else "",
                    pm.cer_breakdown.insertions if pm.cer_breakdown else "",
                    pm.wer_breakdown.substitutions if pm.wer_breakdown else "",
                    pm.wer_breakdown.deletions if pm.wer_breakdown else "",
                    pm.wer_breakdown.insertions if pm.wer_breakdown else "",
                    f"{pm.bbox_metrics.precision:.4f}" if pm.bbox_metrics else "",
                    f"{pm.bbox_metrics.recall:.4f}" if pm.bbox_metrics else "",
                    f"{pm.bbox_metrics.f1:.4f}" if pm.bbox_metrics else "",
                    f"{pm.bbox_metrics.mean_iou:.4f}" if pm.bbox_metrics else "",
                    f"{pm.reading_order_score:.4f}" if pm.reading_order_score is not None else "",
                    pm.message or "",
                ]
                writer.writerow(row)

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "SummaryMetrics":
        """Loads SummaryMetrics from JSON file."""
        target = Path(file_path)
        if not target.is_file():
            raise FileNotFoundError(f"Summary metrics file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)
