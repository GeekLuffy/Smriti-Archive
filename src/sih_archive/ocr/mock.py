"""Mock OCR Adapter for isolated testing and CI evaluation without external binaries (Requirement R3/R7)."""

from datetime import datetime, timezone
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Union
from PIL import Image

from sih_archive.ocr.base import AvailabilityResult, OCRAdapter
from sih_archive.schemas.ocr import OCROutput, ProcessingMetadata, TokenRegion


class MockOCRAdapter(OCRAdapter):
    """
    Authentic mock OCR engine for deterministic, reproducible unit/integration tests
    and offline evaluation pipelines without requiring external binaries (e.g. Tesseract).

    Generates realistic, validated TokenRegions, layout blocks, lines, and bounding boxes
    derived from image dimensions and specified/synthetic text.
    """

    DEFAULT_VERSION = "mock-1.0.0"

    def __init__(
        self,
        version: str = DEFAULT_VERSION,
        default_confidence: float = 95.0,
        mock_data: Optional[Dict[str, str]] = None,
    ):
        """
        Initializes MockOCRAdapter.

        Parameters:
            version: Engine version string.
            default_confidence: Baseline confidence score for generated tokens.
            mock_data: Optional dictionary mapping page_id or image filename to mock text.
        """
        self._version = version
        self._default_confidence = default_confidence
        self._mock_data = mock_data or {}

    def is_available(self) -> AvailabilityResult:
        """Mock engine is always available without external runtime dependencies."""
        return AvailabilityResult(True, f"Mock OCR engine ready ({self._version})")

    def get_version(self) -> str:
        """Returns mock engine version."""
        return self._version

    def get_available_languages(self) -> List[str]:
        """Returns mock supported languages."""
        return ["eng", "mar", "hin"]

    def _generate_synthetic_tokens(
        self,
        text: str,
        img_width: int,
        img_height: int,
    ) -> List[TokenRegion]:
        """
        Generates deterministic, non-overlapping bounding boxes for words in text.
        """
        regions: List[TokenRegion] = []
        if not text.strip():
            return regions

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            words = text.split()
            lines = [" ".join(words[i : i + 10]) for i in range(0, len(words), 10)]

        margin_x = int(img_width * 0.08)
        margin_y = int(img_height * 0.08)
        content_width = max(100, img_width - 2 * margin_x)
        content_height = max(100, img_height - 2 * margin_y)

        num_lines = max(1, len(lines))
        line_height = min(60, max(20, content_height // (num_lines + 1)))
        line_gap = max(4, line_height // 4)

        for line_idx, line in enumerate(lines):
            line_top = margin_y + line_idx * (line_height + line_gap)
            if line_top + line_height > img_height:
                break

            words = line.split()
            if not words:
                continue

            num_words = len(words)
            available_w = content_width - (num_words - 1) * 10
            total_chars = max(1, sum(len(w) for w in words))

            current_x = margin_x
            for word_idx, word in enumerate(words):
                char_ratio = len(word) / total_chars
                w_box = max(20, int(available_w * char_ratio))
                h_box = line_height

                # Ensure box stays within image bounds
                if current_x + w_box > img_width:
                    w_box = max(10, img_width - current_x - 5)

                conf = min(100.0, max(60.0, self._default_confidence - (word_idx % 5)))
                token = TokenRegion(
                    type="word",
                    text=word,
                    bbox=[current_x, line_top, w_box, h_box],
                    confidence=conf,
                    block_num=1,
                    line_num=line_idx + 1,
                    word_num=word_idx + 1,
                )
                regions.append(token)
                current_x += w_box + 10

        return regions

    def process_image(
        self,
        image_path: Union[str, Path],
        language: str = "eng",
        options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> OCROutput:
        """
        Executes mock OCR on the target image and produces standardized OCROutput.
        """
        start_time = time.perf_counter()
        img_p = Path(image_path)
        if not img_p.is_file():
            raise FileNotFoundError(f"Input image not found: {img_p}")

        opt = options or {}
        document_id = opt.get("document_id") or kwargs.get("document_id")
        page_id = opt.get("page_id") or kwargs.get("page_id")
        if not page_id:
            stem = img_p.stem
            m = re.search(r"([a-zA-Z0-9_\-]+_p\d{4})", stem)
            if m:
                page_id = m.group(1)
            else:
                page_id = stem if "_p" in stem else f"{stem}_p0001"
        if not document_id:
            document_id = page_id.split("_p")[0]

        dpi = opt.get("dpi") or kwargs.get("dpi") or 300
        filters = opt.get("filters") or kwargs.get("filters") or ["raw"]

        # Inspect image dimensions
        with Image.open(img_p) as im:
            img_w, img_h = im.size

        # Determine text content
        if "mock_text" in opt:
            text = opt["mock_text"]
        elif "text" in opt:
            text = opt["text"]
        elif img_p.name in self._mock_data:
            text = self._mock_data[img_p.name]
        elif page_id in self._mock_data:
            text = self._mock_data[page_id]
        else:
            # Default canonical text representing archival content without inspecting ground truth
            text = (
                f"Dr. Babasaheb Ambedkar Writings and Speeches\n"
                f"Archival Record Page {page_id}\n"
                f"Preservation and Heritage Benchmark Standard"
            )

        # Generate tokens
        if "mock_regions" in opt and opt["mock_regions"]:
            regions = opt["mock_regions"]
        else:
            regions = self._generate_synthetic_tokens(text, img_w, img_h)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return OCROutput(
            document_id=document_id,
            page_id=page_id,
            language=language,
            script="Latn" if language == "eng" else "Deva",
            engine="mock",
            engine_version=self._version,
            image_path=str(img_p).replace("\\", "/"),
            processing=ProcessingMetadata(dpi=dpi, filters=filters, duration_ms=duration_ms),
            text=text,
            regions=regions,
            status="success",
            error_message=None,
        )
