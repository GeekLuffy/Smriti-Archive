"""OCR engine abstraction and adapters."""

from sih_archive.ocr.base import (
    AvailabilityResult,
    EngineNotFoundError,
    OCRAdapter,
    OCRExecutionError,
    OCRError,
)
from sih_archive.ocr.mock import MockOCRAdapter
from sih_archive.ocr.tesseract import TesseractAdapter

__all__ = [
    "OCRAdapter",
    "AvailabilityResult",
    "OCRError",
    "EngineNotFoundError",
    "OCRExecutionError",
    "TesseractAdapter",
    "MockOCRAdapter",
]
