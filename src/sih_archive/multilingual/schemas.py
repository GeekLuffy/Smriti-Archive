"""
Schemas for Phase E4 Multilingual Translation and Audio Narration.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TranslationRecord(BaseModel):
    """Structured translation output preserving source provenance and verification status."""
    source_text: str = Field(..., description="Original historical text span.")
    translated_text: str = Field(..., description="Machine translated output.")
    source_lang: str = Field(..., pattern="^[a-z]{3}$", description="ISO 639-3 source language.")
    target_lang: str = Field(..., pattern="^[a-z]{3}$", description="ISO 639-3 target language.")
    model_name: str = Field(..., description="Translation model identifier.")
    source_page_id: str = Field(..., description="Originating archival page ID.")
    is_human_verified: bool = Field(default=False, description="Strictly False unless validated by linguistic expert.")
    notes: Optional[str] = Field(None, description="Disclaimers regarding historical idioms or nuances.")


class NarrationRecord(BaseModel):
    """Audio narration record retaining document and page provenance."""
    text: str = Field(..., description="Transcript text being synthesized.")
    audio_path: str = Field(..., description="Relative destination path for generated audio file.")
    language: str = Field(..., pattern="^[a-z]{3}$", description="ISO 639-3 spoken language.")
    voice_model: str = Field(..., description="TTS voice synthesis model identifier.")
    source_page_id: str = Field(..., description="Originating archival page ID.")
    duration_seconds: float = Field(..., ge=0.0, description="Duration of synthesized narration audio.")


class TranslationEvaluation(BaseModel):
    """Qualitative and quantitative metrics for comparing translation adequacy."""
    terminology_adequacy: float = Field(..., ge=0.0, le=1.0, description="Preservation of historical/constitutional terms.")
    fluency_score: float = Field(..., ge=0.0, le=1.0, description="Grammatical and stylistic fluency.")
    source_traceability: float = Field(..., ge=0.0, le=1.0, description="Exact alignment back to source transcript tokens.")
