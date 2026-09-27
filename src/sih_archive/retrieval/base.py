"""
Base Interfaces and Schemas for Phase E2 Retrieval Benchmarking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sih_archive.schemas.ocr import OCROutput, TokenRegion


class SearchResult(BaseModel):
    """Standardized retrieval result item preserving archival provenance."""
    document_id: str = Field(..., description="Archival document identifier.")
    page_id: str = Field(..., description="Archival page identifier.")
    score: float = Field(..., description="Normalized or raw relevance score.")
    text: str = Field(..., description="Matching text excerpt or page transcript.")
    matched_regions: List[TokenRegion] = Field(
        default_factory=list,
        description="Word-level tokens with bounding boxes for visual highlight.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Retrieval engine metadata (e.g. rank, term matches, dense distance).",
    )


class IndexingResult(BaseModel):
    """Statistics emitted upon indexing a batch of OCR outputs."""
    indexed_pages_count: int = Field(..., ge=0)
    total_tokens_count: int = Field(..., ge=0)
    duration_ms: float = Field(..., ge=0.0)
    engine_name: str = Field(...)


class RetrievalEngine(ABC):
    """
    Abstract interface for Phase E2 retrieval engines.
    
    Permits controlled benchmarking across BM25, character n-gram, dense, and hybrid methods.
    """

    @abstractmethod
    def index_documents(self, documents: List[OCROutput]) -> IndexingResult:
        """Indexes a collection of OCR page outputs."""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Executes a search query and returns ranked results."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the canonical name of the retrieval strategy."""
        pass
