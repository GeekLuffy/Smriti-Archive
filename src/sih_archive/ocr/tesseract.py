"""Tesseract OCR Adapter with TSV token extraction and truthful diagnostics (Requirement R3)."""

import csv
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from sih_archive.ocr.base import (
    AvailabilityResult,
    EngineNotFoundError,
    OCRAdapter,
    OCRExecutionError,
)
from sih_archive.schemas.ocr import OCROutput, ProcessingMetadata, TokenRegion


class TesseractAdapter(OCRAdapter):
    """
    Production-grade adapter for Tesseract OCR.

    Queries system PATH and known standard Windows/Linux installation directories.
    Provides structured TSV extraction of word bounding boxes, lines, blocks, and confidence scores.
    Enforces truthful diagnostics when the engine binary is not installed.
    """

    WINDOWS_STANDARD_PATHS = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    ]

    def __init__(self, tesseract_cmd: Optional[Union[str, Path]] = None):
        """
        Initializes the TesseractAdapter.

        Parameters:
            tesseract_cmd: Optional explicit path to the tesseract executable.
        """
        self._explicit_cmd = Path(tesseract_cmd) if tesseract_cmd else None
        self._cached_binary: Optional[Path] = None
        self._cached_version: Optional[str] = None

    def _resolve_binary(self) -> Optional[Path]:
        """Resolves the Tesseract binary path with multi-tier discovery."""
        if self._cached_binary and self._cached_binary.is_file():
            return self._cached_binary

        # 1. Explicit path passed to constructor
        if self._explicit_cmd:
            if self._explicit_cmd.is_file():
                self._cached_binary = self._explicit_cmd
                return self._cached_binary
            # If explicit path was given but invalid, return None
            return None

        # 2. Environment variable overrides
        env_cmd = os.environ.get("TESSERACT_CMD") or os.environ.get("TESSERACT_PATH")
        if env_cmd:
            p = Path(env_cmd)
            if p.is_file():
                self._cached_binary = p
                return self._cached_binary

        # 3. System PATH lookup
        path_which = shutil.which("tesseract") or shutil.which("tesseract.exe")
        if path_which:
            p = Path(path_which)
            if p.is_file():
                self._cached_binary = p
                return self._cached_binary

        # 4. Standard Windows locations
        for win_path in self.WINDOWS_STANDARD_PATHS:
            if win_path.is_file():
                self._cached_binary = win_path
                return self._cached_binary

        return None

    def is_available(self) -> AvailabilityResult:
        """
        Verifies whether Tesseract binary is installed and executable.

        Returns:
            AvailabilityResult: (available: bool, message: str)
        """
        binary = self._resolve_binary()
        if not binary:
            searched = [
                "explicit cmd: " + str(self._explicit_cmd) if self._explicit_cmd else None,
                "env TESSERACT_CMD/TESSERACT_PATH",
                "system PATH lookup",
            ] + [str(p) for p in self.WINDOWS_STANDARD_PATHS]
            searched_clean = [s for s in searched if s]
            msg = (
                "Tesseract OCR binary not found. Searched: "
                + ", ".join(searched_clean)
                + ". Remediation: Install Tesseract on Windows via 'winget install UB-Mannheim.TesseractOCR' "
                + "or on Linux via 'sudo apt-get install tesseract-ocr', or pass --tesseract-cmd."
            )
            return AvailabilityResult(False, msg)

        try:
            res = subprocess.run(
                [str(binary), "--version"],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            if res.returncode == 0:
                first_line = res.stdout.splitlines()[0].strip() if res.stdout else "Tesseract ready"
                self._cached_version = first_line
                return AvailabilityResult(True, f"Tesseract ready: {first_line} at {binary}")
            return AvailabilityResult(False, f"Tesseract binary returned error code {res.returncode}: {res.stderr}")
        except Exception as e:
            return AvailabilityResult(False, f"Failed to execute Tesseract binary at {binary}: {e}")

    def get_version(self) -> str:
        """Returns Tesseract version string."""
        avail, msg = self.is_available()
        if not avail:
            raise EngineNotFoundError(msg)
        if self._cached_version:
            return self._cached_version
        binary = self._resolve_binary()
        res = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=True,
        )
        version_line = res.stdout.splitlines()[0].strip()
        self._cached_version = version_line
        return version_line

    def get_available_languages(self) -> List[str]:
        """Returns list of installed Tesseract language codes."""
        avail, _ = self.is_available()
        if not avail:
            return []
        binary = self._resolve_binary()
        try:
            res = subprocess.run(
                [str(binary), "--list-langs"],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=True,
            )
            langs = []
            for line in res.stdout.splitlines():
                line = line.strip()
                if line and not line.lower().startswith("list of"):
                    langs.append(line)
            return langs
        except Exception:
            return ["eng"]

    # Backward compatibility alias
    get_installed_languages = get_available_languages

    @staticmethod
    def parse_tsv_output(tsv_text: str) -> Tuple[str, List[TokenRegion]]:
        """
        Parses raw Tesseract TSV output into reconstructed text and TokenRegion list.

        TSV Columns:
            level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
        """
        regions: List[TokenRegion] = []
        if not tsv_text.strip():
            return "", regions

        reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
        lines_dict: Dict[Tuple[int, int, int], List[str]] = {}

        for row in reader:
            try:
                level = int(row.get("level", 0))
                # level 5 is word level
                if level != 5:
                    continue

                text = row.get("text", "")
                if text is None or not text.strip():
                    continue

                conf_val = float(row.get("conf", -1))
                if conf_val < 0:
                    continue

                # Clamp confidence between 0.0 and 100.0
                confidence = max(0.0, min(100.0, conf_val))

                left = max(0, int(row.get("left", 0)))
                top = max(0, int(row.get("top", 0)))
                width = max(0, int(row.get("width", 0)))
                height = max(0, int(row.get("height", 0)))

                block_num = int(row.get("block_num", 0))
                par_num = int(row.get("par_num", 0))
                line_num = int(row.get("line_num", 0))
                word_num = int(row.get("word_num", 0))

                cleaned_text = text.strip()

                region = TokenRegion(
                    type="word",
                    text=cleaned_text,
                    bbox=[left, top, width, height],
                    confidence=confidence,
                    block_num=block_num,
                    line_num=line_num,
                    word_num=word_num,
                )
                regions.append(region)

                line_key = (block_num, par_num, line_num)
                if line_key not in lines_dict:
                    lines_dict[line_key] = []
                lines_dict[line_key].append(cleaned_text)

            except (ValueError, TypeError):
                continue

        # Reconstruct page text line by line
        reconstructed_lines = [" ".join(words) for words in lines_dict.values()]
        full_text = "\n".join(reconstructed_lines)

        return full_text, regions

    def process_image(
        self,
        image_path: Union[str, Path],
        language: str = "eng",
        options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> OCROutput:
        """
        Runs Tesseract OCR on the target image and produces structured OCROutput.
        """
        opt = options or {}
        img_p = Path(image_path)
        if not img_p.is_file():
            raise FileNotFoundError(f"Input image not found: {img_p}")

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
        timeout_seconds = opt.get("timeout_seconds") or kwargs.get("timeout_seconds") or 30.0
        raise_on_error = opt.get("raise_on_error", False)

        avail, avail_msg = self.is_available()
        if not avail:
            if raise_on_error:
                raise EngineNotFoundError(avail_msg)
            return OCROutput(
                document_id=document_id,
                page_id=page_id,
                language=language,
                engine="tesseract",
                engine_version=None,
                image_path=str(img_p).replace("\\", "/"),
                processing=ProcessingMetadata(dpi=dpi, filters=filters, duration_ms=0.0),
                text="",
                regions=[],
                status="engine_unavailable",
                error_message=avail_msg,
            )

        binary = self._resolve_binary()
        cmd = [
            str(binary),
            str(img_p),
            "stdout",
            "-l",
            language,
            "--dpi",
            str(dpi),
            "tsv",
        ]

        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            if proc.returncode != 0:
                err_msg = f"Tesseract execution failed with code {proc.returncode}: {proc.stderr}"
                if raise_on_error:
                    raise OCRExecutionError(err_msg)
                return OCROutput(
                    document_id=document_id,
                    page_id=page_id,
                    language=language,
                    engine="tesseract",
                    engine_version=self.get_version(),
                    image_path=str(img_p).replace("\\", "/"),
                    processing=ProcessingMetadata(dpi=dpi, filters=filters, duration_ms=duration_ms),
                    text="",
                    regions=[],
                    status="error",
                    error_message=err_msg,
                )

            text, regions = self.parse_tsv_output(proc.stdout)
            return OCROutput(
                document_id=document_id,
                page_id=page_id,
                language=language,
                engine="tesseract",
                engine_version=self.get_version(),
                image_path=str(img_p).replace("\\", "/"),
                processing=ProcessingMetadata(dpi=dpi, filters=filters, duration_ms=duration_ms),
                text=text,
                regions=regions,
                status="success",
                error_message=None,
            )

        except subprocess.TimeoutExpired as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = f"Tesseract process timed out after {timeout_seconds} seconds on {img_p}."
            if raise_on_error:
                raise OCRExecutionError(err_msg) from e
            return OCROutput(
                document_id=document_id,
                page_id=page_id,
                language=language,
                engine="tesseract",
                engine_version=self._cached_version,
                image_path=str(img_p).replace("\\", "/"),
                processing=ProcessingMetadata(dpi=dpi, filters=filters, duration_ms=duration_ms),
                text="",
                regions=[],
                status="error",
                error_message=err_msg,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = f"Unexpected error during Tesseract OCR: {e}"
            if raise_on_error:
                raise OCRExecutionError(err_msg) from e
            return OCROutput(
                document_id=document_id,
                page_id=page_id,
                language=language,
                engine="tesseract",
                engine_version=self._cached_version,
                image_path=str(img_p).replace("\\", "/"),
                processing=ProcessingMetadata(dpi=dpi, filters=filters, duration_ms=duration_ms),
                text="",
                regions=[],
                status="error",
                error_message=err_msg,
            )
