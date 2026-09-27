"""Pydantic schemas for rendered page provenance and rendering manifests."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class PageProvenance(BaseModel):
    """Provenance record for an individual rendered page image."""

    document_id: str = Field(..., description="Identifier of the source archival document.")
    page_id: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_\-]+_p\d{4}$",
        description="Deterministic page identifier, e.g., 'ambedkar_speech_vol1_p0001'.",
    )
    page_number: int = Field(..., ge=1, description="1-indexed page number in the source PDF.")
    width: int = Field(..., ge=1, description="Rendered image width in pixels.")
    height: int = Field(..., ge=1, description="Rendered image height in pixels.")
    orig_width_pt: Optional[float] = Field(default=None, description="Original page width in PDF points (1/72 in).")
    orig_height_pt: Optional[float] = Field(default=None, description="Original page height in PDF points (1/72 in).")
    rotation: int = Field(default=0, description="Page rotation in degrees (0, 90, 180, 270).")
    dpi: int = Field(..., ge=72, le=1200, description="Rendering resolution in dots per inch.")
    source_pdf: str = Field(..., description="Relative or absolute path to the source PDF.")
    source_pdf_sha256: Optional[str] = Field(default=None, description="SHA-256 hash of the source PDF.")
    image_path: str = Field(..., description="Relative or absolute path to the saved PNG image.")
    sha256: str = Field(..., pattern=r"^[a-fA-F0-9]{64}$", description="SHA-256 hash of the rendered PNG image.")
    rendered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when the page was rendered.",
    )
    status: str = Field(
        default="rendered",
        description="Rendering status ('rendered' or 'cached').",
    )

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Serializes page provenance to a JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "PageProvenance":
        """Deserializes page provenance from a JSON file."""
        target = Path(file_path)
        with open(target, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())


class DocumentRenderingManifest(BaseModel):
    """Unified provenance manifest summarizing all rendered pages for a document."""

    document_id: str = Field(..., description="Identifier of the source archival document.")
    source_pdf: str = Field(..., description="Path to the source PDF.")
    source_pdf_sha256: Optional[str] = Field(default=None, description="SHA-256 hash of the source PDF.")
    dpi: int = Field(..., description="Rendering resolution in DPI.")
    total_pages_in_pdf: int = Field(..., ge=1, description="Total number of pages in the PDF.")
    rendered_pages_count: int = Field(..., ge=0, description="Count of pages rendered in this run.")
    pages: List[PageProvenance] = Field(default_factory=list, description="List of page provenance records.")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of manifest generation.",
    )

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Serializes document rendering manifest to a JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "DocumentRenderingManifest":
        """Deserializes document rendering manifest from a JSON file."""
        target = Path(file_path)
        with open(target, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())
