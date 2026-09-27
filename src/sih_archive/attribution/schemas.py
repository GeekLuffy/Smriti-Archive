"""
Schemas and Data Contracts for Phase E3 Evidence-Grounded Attribution.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """Specific citation pointing to an archival source document, page, and coordinate bounding box."""
    document_id: str = Field(..., description="Archival document identifier.")
    page_id: str = Field(..., description="Archival page identifier.")
    quote_span: str = Field(..., description="Exact textual excerpt supporting the claim.")
    bbox: Optional[List[int]] = Field(
        None,
        description="Pixel coordinates [x, y, w, h] on rendered 300 DPI page.",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class AttributedClaim(BaseModel):
    """Individual factual statement with verifiable source citation."""
    claim_text: str = Field(..., description="Factual claim or sentence in the answer.")
    citation: Optional[SourceCitation] = Field(None, description="Supporting evidence citation.")
    is_supported: bool = Field(..., description="True if evidence verifies claim; False if ungrounded.")


class GroundedAnswer(BaseModel):
    """Complete answer with sentence-level claim attribution and explicit refusal handling."""
    question: str = Field(..., description="Input user research question.")
    answer_text: str = Field(..., description="Synthesized answer or refusal notice.")
    claims: List[AttributedClaim] = Field(default_factory=list, description="Claim-level attributions.")
    is_refusal: bool = Field(default=False, description="True if system refused to answer due to insufficient evidence.")
    refusal_reason: Optional[str] = Field(None, description="Explanation for refusal if ungrounded.")
    retrieved_page_ids: List[str] = Field(default_factory=list, description="Page IDs consulted by retrieval.")


class AttributionMetrics(BaseModel):
    """Evaluation summary for Phase E3 evidence grounding benchmarks."""
    total_questions: int = Field(..., ge=0)
    claim_support_rate: float = Field(..., ge=0.0, le=1.0, description="Proportion of claims verified by cited evidence.")
    span_precision: float = Field(..., ge=0.0, le=1.0, description="Token precision of cited quote spans against reference facts.")
    mean_bbox_iou: float = Field(..., ge=0.0, le=1.0, description="Mean IoU overlap between cited bboxes and true target regions.")
    broken_citation_rate: float = Field(..., ge=0.0, le=1.0, description="Proportion of citations referencing nonexistent pages/spans.")
    source_page_accuracy: float = Field(..., ge=0.0, le=1.0, description="Proportion of answers citing the correct source page.")
    unsupported_answer_rate: float = Field(..., ge=0.0, le=1.0, description="Proportion of answers containing unverified claims.")
