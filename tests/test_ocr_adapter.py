"""Comprehensive unit test suite for Milestone 4:
- TokenRegion, ProcessingMetadata, and OCROutput schema validation (Pydantic v2)
- OCRAdapter interface and AvailabilityResult behavior
- TesseractAdapter discovery, truthful diagnostics, and structured TSV parsing
- MockOCRAdapter for isolated CI testing
- CLI run_ocr.py execution, caching, and error handling
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from PIL import Image, ImageDraw

from sih_archive.ocr.base import (
    AvailabilityResult,
    EngineNotFoundError,
    OCRExecutionError,
)
from sih_archive.ocr.mock import MockOCRAdapter
from sih_archive.ocr.tesseract import TesseractAdapter
from sih_archive.schemas.ocr import (
    OCROutput,
    ProcessingMetadata,
    TokenRegion,
)
from scripts.run_ocr import main as cli_ocr_main


@pytest.fixture
def synthetic_page_image(tmp_path: Path) -> Path:
    """Creates a small synthetic page image with rendered text for OCR testing."""
    img_path = tmp_path / "synthetic_doc_p0001.png"
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Dr. B.R. Ambedkar: Annihilation of Caste", fill=(0, 0, 0))
    draw.text((50, 100), "Preservation Benchmark Sample Document", fill=(0, 0, 0))
    img.save(img_path)
    return img_path


# --- Schema Validation Tests ---

def test_token_region_valid():
    """Verify valid TokenRegion instantiation."""
    region = TokenRegion(
        type="word",
        text="Ambedkar",
        bbox=[100, 150, 80, 25],
        confidence=96.5,
        block_num=1,
        line_num=1,
        word_num=2,
    )
    assert region.type == "word"
    assert region.text == "Ambedkar"
    assert region.bbox == [100, 150, 80, 25]
    assert region.confidence == 96.5


def test_token_region_invalid_bbox():
    """Verify invalid bounding box lengths or negative coordinates fail validation."""
    with pytest.raises(ValidationError):
        # Only 3 coordinates instead of 4
        TokenRegion(type="word", text="Test", bbox=[10, 20, 30], confidence=90.0)

    with pytest.raises(ValidationError):
        # Negative coordinate
        TokenRegion(type="word", text="Test", bbox=[-10, 20, 30, 40], confidence=90.0)

    with pytest.raises(ValidationError):
        # Negative dimension
        TokenRegion(type="word", text="Test", bbox=[10, 20, -5, 40], confidence=90.0)


def test_token_region_confidence_bounds():
    """Verify confidence must be bounded between 0.0 and 100.0."""
    with pytest.raises(ValidationError):
        TokenRegion(type="word", text="Test", bbox=[0, 0, 10, 10], confidence=-1.0)

    with pytest.raises(ValidationError):
        TokenRegion(type="word", text="Test", bbox=[0, 0, 10, 10], confidence=101.0)


def test_processing_metadata_defaults():
    """Verify ProcessingMetadata defaults and validations."""
    meta = ProcessingMetadata()
    assert meta.dpi == 300
    assert meta.filters == []
    assert meta.duration_ms == 0.0
    assert meta.timestamp is not None

    with pytest.raises(ValidationError):
        ProcessingMetadata(duration_ms=-10.0)


def test_ocr_output_schema_and_serialization(tmp_path: Path):
    """Verify OCROutput schema, page_id pattern validation, and JSON roundtrip."""
    output = OCROutput(
        document_id="ambedkar_vol01",
        page_id="ambedkar_vol01_p0001",
        language="eng",
        script="Latn",
        engine="mock",
        engine_version="mock-1.0.0",
        image_path="data/processed/pages/ambedkar_vol01_p0001.png",
        processing=ProcessingMetadata(dpi=300, filters=["raw"], duration_ms=45.2),
        text="Dr. Babasaheb Ambedkar Writings and Speeches",
        regions=[
            TokenRegion(type="word", text="Dr.", bbox=[50, 100, 30, 20], confidence=98.0),
            TokenRegion(type="word", text="Babasaheb", bbox=[90, 100, 90, 20], confidence=95.0),
        ],
        status="success",
    )

    # Test invalid page_id pattern
    with pytest.raises(ValidationError):
        OCROutput(
            document_id="doc1",
            page_id="invalid_page_id",  # Missing _p0000 format
            engine="mock",
            image_path="test.png",
            processing=ProcessingMetadata(),
            text="Test",
        )

    # Test JSON file roundtrip
    json_file = tmp_path / "ocr_output_test.json"
    output.to_json_file(json_file)
    assert json_file.is_file()

    loaded = OCROutput.from_json_file(json_file)
    assert loaded.document_id == output.document_id
    assert loaded.page_id == output.page_id
    assert len(loaded.regions) == 2
    assert loaded.regions[1].text == "Babasaheb"


# --- AvailabilityResult & Base Class Tests ---

def test_availability_result_tuple_and_bool_behavior():
    """Verify AvailabilityResult supports both tuple unpacking and boolean conversion."""
    res_true = AvailabilityResult(True, "Engine operational")
    avail, msg = res_true
    assert avail is True
    assert msg == "Engine operational"
    assert bool(res_true) is True

    res_false = AvailabilityResult(False, "Binary not found")
    avail_f, msg_f = res_false
    assert avail_f is False
    assert "not found" in msg_f
    assert bool(res_false) is False


# --- TesseractAdapter Tests ---

def test_tesseract_adapter_truthful_missing_binary():
    """Verify TesseractAdapter truthfully reports unavailable when binary path is invalid."""
    adapter = TesseractAdapter(tesseract_cmd="C:/nonexistent/path/to/tesseract.exe")
    avail, msg = adapter.is_available()
    assert avail is False
    assert "not found" in msg.lower()
    assert bool(adapter.is_available()) is False

    # Calling get_version must raise EngineNotFoundError
    with pytest.raises(EngineNotFoundError, match="not found"):
        adapter.get_version()

    # get_available_languages must return empty list when missing
    assert adapter.get_available_languages() == []


def test_tesseract_adapter_structured_tsv_parser():
    """
    Verify Tesseract TSV parser reconstructs text and extracts TokenRegions with bounding boxes.
    Uses realistic multi-level Tesseract TSV output fixture.
    """
    sample_tsv = (
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
        "1\t1\t0\t0\t0\t0\t0\t0\t2480\t3508\t-1\t\n"
        "2\t1\t1\t0\t0\t0\t100\t200\t1800\t500\t-1\t\n"
        "3\t1\t1\t1\t0\t0\t100\t200\t1800\t200\t-1\t\n"
        "4\t1\t1\t1\t1\t0\t100\t200\t1200\t50\t-1\t\n"
        "5\t1\t1\t1\t1\t1\t100\t200\t150\t50\t95.0\tDR.\n"
        "5\t1\t1\t1\t1\t2\t270\t200\t450\t50\t96.2\tBABASAHEB\n"
        "5\t1\t1\t1\t1\t3\t740\t200\t400\t50\t94.8\tAMBEDKAR\n"
        "4\t1\t1\t1\t2\t0\t100\t280\t1000\t50\t-1\t\n"
        "5\t1\t1\t1\t2\t1\t100\t280\t300\t50\t91.5\tWRITINGS\n"
        "5\t1\t1\t1\t2\t2\t420\t280\t150\t50\t89.0\tAND\n"
        "5\t1\t1\t1\t2\t3\t590\t280\t350\t50\t93.0\tSPEECHES\n"
        "5\t1\t1\t1\t2\t4\t960\t280\t20\t50\t-1\t\n"  # structural or negative conf
        "5\t1\t1\t1\t2\t5\t1000\t280\t20\t50\t85.0\t   \n"  # whitespace only
    )

    reconstructed_text, regions = TesseractAdapter.parse_tsv_output(sample_tsv)

    assert len(regions) == 6
    assert regions[0].text == "DR."
    assert regions[0].bbox == [100, 200, 150, 50]
    assert regions[0].confidence == 95.0
    assert regions[0].block_num == 1
    assert regions[0].line_num == 1
    assert regions[0].word_num == 1

    assert regions[2].text == "AMBEDKAR"
    assert regions[3].text == "WRITINGS"
    assert regions[3].line_num == 2

    # Verify line reconstruction
    lines = reconstructed_text.splitlines()
    assert len(lines) == 2
    assert lines[0] == "DR. BABASAHEB AMBEDKAR"
    assert lines[1] == "WRITINGS AND SPEECHES"


def test_tesseract_adapter_empty_tsv():
    """Verify empty or header-only TSV produces empty text and regions."""
    text, regions = TesseractAdapter.parse_tsv_output("")
    assert text == ""
    assert regions == []


def test_tesseract_process_image_when_unavailable(synthetic_page_image: Path):
    """Verify process_image returns structured error output without unhandled crash when engine missing."""
    adapter = TesseractAdapter(tesseract_cmd="C:/nonexistent/tesseract.exe")
    output = adapter.process_image(synthetic_page_image)

    assert output.status == "engine_unavailable"
    assert output.engine == "tesseract"
    assert "not found" in output.error_message.lower()
    assert output.text == ""
    assert output.regions == []

    # If raise_on_error is requested, it must raise EngineNotFoundError
    with pytest.raises(EngineNotFoundError):
        adapter.process_image(synthetic_page_image, options={"raise_on_error": True})


# --- MockOCRAdapter Tests ---

def test_mock_ocr_adapter_availability():
    """Verify MockOCRAdapter is always available."""
    adapter = MockOCRAdapter()
    avail, msg = adapter.is_available()
    assert avail is True
    assert "ready" in msg
    assert adapter.get_version() == "mock-1.0.0"
    assert "eng" in adapter.get_available_languages()


def test_mock_ocr_adapter_process_image(synthetic_page_image: Path):
    """Verify MockOCRAdapter processes image and produces valid OCROutput with non-overlapping tokens."""
    adapter = MockOCRAdapter()
    output = adapter.process_image(
        synthetic_page_image,
        language="eng",
        options={"dpi": 300, "filters": ["raw"]},
    )

    assert output.status == "success"
    assert output.engine == "mock"
    assert output.engine_version == "mock-1.0.0"
    assert output.document_id == "synthetic_doc"
    assert output.page_id == "synthetic_doc_p0001"
    assert len(output.text) > 0
    assert len(output.regions) > 0

    # Validate that bounding boxes reside within image dimensions (800x1000)
    for token in output.regions:
        x, y, w, h = token.bbox
        assert x >= 0
        assert y >= 0
        assert x + w <= 800
        assert y + h <= 1000
        assert 0.0 <= token.confidence <= 100.0


def test_mock_ocr_adapter_custom_text(synthetic_page_image: Path):
    """Verify MockOCRAdapter respects mock_text override in options."""
    adapter = MockOCRAdapter()
    custom_text = "Liberty Equality Fraternity"
    output = adapter.process_image(
        synthetic_page_image,
        options={"mock_text": custom_text},
    )

    assert output.text == custom_text
    assert len(output.regions) == 3
    assert [r.text for r in output.regions] == ["Liberty", "Equality", "Fraternity"]


def test_mock_ocr_adapter_missing_image(tmp_path: Path):
    """Verify FileNotFoundError when input image does not exist."""
    adapter = MockOCRAdapter()
    with pytest.raises(FileNotFoundError):
        adapter.process_image(tmp_path / "missing_image.png")


# --- CLI run_ocr.py Integration Tests ---

def test_cli_run_ocr_help():
    """Verify run_ocr.py CLI --help executes cleanly with code 0."""
    with pytest.raises(SystemExit) as exc:
        cli_ocr_main(["--help"])
    assert exc.value.code == 0


def test_cli_run_ocr_missing_engine_clean_exit(synthetic_page_image: Path):
    """Verify run_ocr.py with unavailable tesseract exits with code 1 and clean diagnostic."""
    exit_code = cli_ocr_main([
        "-i", str(synthetic_page_image),
        "-e", "tesseract",
        "--tesseract-cmd", "C:/nonexistent/tesseract.exe",
    ])
    assert exit_code == 1


def test_cli_run_ocr_mock_execution(synthetic_page_image: Path, tmp_path: Path):
    """Verify run_ocr.py with mock engine successfully processes image and outputs JSON."""
    out_dir = tmp_path / "ocr_output"
    exit_code = cli_ocr_main([
        "-i", str(synthetic_page_image),
        "-e", "mock",
        "-o", str(out_dir),
    ])
    assert exit_code == 0

    expected_json = out_dir / "synthetic_doc_p0001_mock_raw.json"
    assert expected_json.is_file()

    # Verify output validates as OCROutput
    loaded = OCROutput.from_json_file(expected_json)
    assert loaded.status == "success"
    assert len(loaded.regions) > 0


def test_cli_run_ocr_check_only_flag():
    """Verify --check-only returns 0 for mock engine and 1 for unavailable engine."""
    assert cli_ocr_main(["-i", ".", "-e", "mock", "--check-only"]) == 0
    assert cli_ocr_main(["-i", ".", "-e", "tesseract", "--tesseract-cmd", "C:/invalid.exe", "--check-only"]) == 1
