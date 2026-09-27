"""Base classes and interfaces for OCR adapters (Requirement R3)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Tuple, Union

from sih_archive.schemas.ocr import OCROutput


class AvailabilityResult(NamedTuple):
    """Result of an adapter availability check, supporting both tuple unpacking and bool check."""

    available: bool
    message: str

    def __bool__(self) -> bool:
        return bool(self.available)


class OCRError(Exception):
    """Base exception for all OCR adapter errors."""
    pass


class EngineNotFoundError(OCRError):
    """Raised when an external OCR engine binary is not installed or located."""
    pass


class OCRExecutionError(OCRError):
    """Raised when an OCR engine process fails or times out during execution."""
    pass


class OCRAdapter(ABC):
    """Abstract base class defining the contract for all OCR engine adapters."""

    @abstractmethod
    def is_available(self) -> AvailabilityResult:
        """
        Verifies whether the underlying OCR engine is installed and operational.

        Returns:
            AvailabilityResult: NamedTuple (available: bool, message: str)
            Evaluates as True/False in boolean contexts and supports 2-tuple unpacking.
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        Returns the version string of the underlying OCR engine.

        Raises:
            EngineNotFoundError: If the engine binary cannot be executed.
        """
        pass

    @abstractmethod
    def process_image(
        self,
        image_path: Union[str, Path],
        language: str = "eng",
        options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> OCROutput:
        """
        Executes OCR on the given image file and returns standardized OCROutput.

        Parameters:
            image_path: Path to the target image file.
            language: ISO 639-3 language code (default 'eng').
            options: Optional execution parameters (dpi, filters, timeout, document_id, page_id).

        Returns:
            OCROutput: Validated Pydantic model capturing text and positional token regions.
        """
        pass

    def get_available_languages(self) -> list[str]:
        """Returns list of installed/supported language codes. Default implementation."""
        return ["eng"]

    def diagnose(self) -> Dict[str, Any]:
        """Returns diagnostic dictionary with installation status, binary path, and remediation."""
        avail, msg = self.is_available()
        return {
            "engine": self.__class__.__name__,
            "available": avail,
            "message": msg,
            "version": self.get_version() if avail else None,
        }
