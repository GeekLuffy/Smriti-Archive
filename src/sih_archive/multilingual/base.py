"""
Interfaces and Mock Adapters for Multilingual Translation and Speech Synthesis.
"""

from abc import ABC, abstractmethod
from typing import Optional
from sih_archive.multilingual.schemas import NarrationRecord, TranslationRecord


class TranslationAdapter(ABC):
    """Abstract interface for multilingual translation engines."""

    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        source_page_id: str,
    ) -> TranslationRecord:
        """Translates text from source language to target language while retaining page identity."""
        pass


class TTSAdapter(ABC):
    """Abstract interface for audio narration and speech synthesis."""

    @abstractmethod
    def synthesize_speech(
        self,
        text: str,
        language: str,
        source_page_id: str,
        output_audio_path: str,
    ) -> NarrationRecord:
        """Synthesizes speech audio for an archival text passage."""
        pass


class MockTranslationAdapter(TranslationAdapter):
    """Offline test translation adapter preserving research provenance."""

    def __init__(self, model_name: str = "mock_translator_v1"):
        self.model_name = model_name

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        source_page_id: str,
    ) -> TranslationRecord:
        # Mock translation appends language tag without fabricating linguistic fluency
        translated = f"[{target_lang.upper()}_TRANSLATION] {text}"
        return TranslationRecord(
            source_text=text,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            model_name=self.model_name,
            source_page_id=source_page_id,
            is_human_verified=False,
            notes="Machine translation prototype output; not historically verified.",
        )


class MockTTSAdapter(TTSAdapter):
    """Offline test speech synthesis adapter."""

    def __init__(self, voice_model: str = "mock_indic_tts_v1"):
        self.voice_model = voice_model

    def synthesize_speech(
        self,
        text: str,
        language: str,
        source_page_id: str,
        output_audio_path: str,
    ) -> NarrationRecord:
        estimated_duration = max(1.0, round(len(text.split()) / 2.5, 2))
        return NarrationRecord(
            text=text,
            audio_path=output_audio_path,
            language=language,
            voice_model=self.voice_model,
            source_page_id=source_page_id,
            duration_seconds=estimated_duration,
        )
