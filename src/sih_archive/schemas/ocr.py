"""Pydantic schemas for OCR tokens, processing metadata, and OCR output records."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


RegionType = Literal["word", "line", "block"]
OCRStatus = Literal["success", "engine_unavailable", "error"]


class TokenRegion(BaseModel):
    """Positional token, word, line, or block region with bounding box and confidence."""

    type: RegionType = Field(default="word", description="Hierarchy level: 'word', 'line', or 'block'.")
    text: str = Field(..., description="Text content within this token region.")
    bbox: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box coordinates [x, y, w, h] in absolute image pixels.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="OCR engine confidence score ranging from 0.0 to 100.0.",
    )
    block_num: Optional[int] = Field(default=None, description="Layout block index.")
    line_num: Optional[int] = Field(default=None, description="Line index within the layout block.")
    word_num: Optional[int] = Field(default=None, description="Word index within the line.")

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: List[int]) -> List[int]:
        if len(v) != 4:
            raise ValueError("Bounding box must contain exactly 4 integers: [x, y, w, h].")
        x, y, w, h = v
        if x < 0 or y < 0:
            raise ValueError(f"Bounding box origin coordinates (x={x}, y={y}) cannot be negative.")
        if w < 0 or h < 0:
            raise ValueError(f"Bounding box dimensions (w={w}, h={h}) cannot be negative.")
        return v


class ProcessingMetadata(BaseModel):
    """Metadata capturing preprocessing pipeline filters and OCR execution metrics."""

    dpi: int = Field(default=300, ge=72, le=1200, description="Image resolution in DPI.")
    filters: List[str] = Field(
        default_factory=list,
        description="Ordered list of preprocessing filter names applied before OCR (e.g. ['raw'] or ['grayscale', 'otsu']).",
    )
    duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="OCR execution latency in milliseconds.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC execution timestamp.",
    )


class OCROutput(BaseModel):
    """Standardized OCR output document capturing full text and positional tokens."""

    document_id: str = Field(..., description="Source document identifier.")
    page_id: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_\-]+_p\d{4}$",
        description="Deterministic page identifier, e.g. 'ambedkar_speech_vol1_p0001'.",
    )
    language: str = Field(default="eng", description="Language code passed to the OCR engine (e.g., 'eng', 'mar').")
    script: Optional[str] = Field(default=None, description="ISO 15924 script code (e.g., 'Latn', 'Deva').")
    engine: str = Field(..., description="OCR engine identifier ('tesseract', 'mock', etc.).")
    engine_version: Optional[str] = Field(default=None, description="Version string of the OCR engine.")
    image_path: str = Field(..., description="Path to the processed image file.")
    processing: ProcessingMetadata = Field(..., description="Processing metadata including DPI and filter sequence.")
    text: str = Field(default="", description="Full reconstructed text for the page.")
    regions: List[TokenRegion] = Field(
        default_factory=list,
        description="List of detected token regions with bounding boxes and confidence scores.",
    )
    status: OCRStatus = Field(
        default="success",
        description="OCR status: 'success', 'engine_unavailable', or 'error'.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Diagnostic error message if status is 'engine_unavailable' or 'error'.",
    )

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Serializes OCR output to a formatted JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "OCROutput":
        """Deserializes OCR output from a JSON file."""
        target = Path(file_path)
        with open(target, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())
