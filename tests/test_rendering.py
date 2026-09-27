"""Comprehensive unit test suite for Milestone 3:
- Deterministic PDF to Page Image Rendering Pipeline (Requirement R2)
- Resolution scaling (DPI / 72.0)
- Deterministic page ID naming ({document_id}_p{page_num:04d})
- Provenance manifest emission
- Duplicate rendering prevention / caching
- CLI invocation and argument validation
"""

import json
from pathlib import Path
import tempfile
import pytest
import pymupdf as fitz

from sih_archive.rendering.pdf import (
    compute_sha256,
    get_pdf_metadata,
    parse_page_range,
    render_pdf,
)
from sih_archive.schemas.rendering import DocumentRenderingManifest, PageProvenance
from scripts.render_pdf import main as cli_main


@pytest.fixture
def synthetic_pdf(tmp_path: Path) -> Path:
    """Creates a 3-page synthetic test PDF with known dimensions and text."""
    pdf_path = tmp_path / "synthetic_archival_doc.pdf"
    doc = fitz.open()

    # Page 1: Standard A4 (595 x 842 pt)
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 100), "Dr. B.R. Ambedkar: Annihilation of Caste", fontsize=16)
    p1.insert_text((50, 140), "Historical Archival Preservation Benchmark", fontsize=12)

    # Page 2: Standard A4
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((50, 100), "Section II: Social Democracy and Rights", fontsize=14)

    # Page 3: Standard A4
    p3 = doc.new_page(width=595, height=842)
    p3.insert_text((50, 100), "Section III: Statistical Appendix", fontsize=14)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


# --- Page Range Parsing Tests ---

def test_parse_page_range_all():
    """Verify 'all', None, and empty string return complete page index list."""
    assert parse_page_range("all", 5) == [1, 2, 3, 4, 5]
    assert parse_page_range(None, 3) == [1, 2, 3]
    assert parse_page_range("", 4) == [1, 2, 3, 4]


def test_parse_page_range_single_and_ranges():
    """Verify single numbers, ranges, and comma-separated expressions."""
    assert parse_page_range("2", 5) == [2]
    assert parse_page_range(3, 5) == [3]
    assert parse_page_range("1-3", 5) == [1, 2, 3]
    assert parse_page_range("1,3,5", 5) == [1, 3, 5]
    assert parse_page_range("1-2,4-5", 5) == [1, 2, 4, 5]
    assert parse_page_range([1, 4], 5) == [1, 4]


def test_parse_page_range_invalid_bounds():
    """Verify out-of-range or malformed page expressions raise ValueError."""
    with pytest.raises(ValueError, match="out of range"):
        parse_page_range("0", 5)

    with pytest.raises(ValueError, match="out of range"):
        parse_page_range("6", 5)

    with pytest.raises(ValueError, match="Invalid range"):
        parse_page_range("4-2", 5)

    with pytest.raises(ValueError, match="Invalid range"):
        parse_page_range("1-10", 5)

    with pytest.raises(ValueError, match="Malformed"):
        parse_page_range("1-a", 5)


# --- PDF Metadata & Checksum Tests ---

def test_get_pdf_metadata(synthetic_pdf: Path):
    """Verify metadata extraction on synthetic PDF."""
    meta = get_pdf_metadata(synthetic_pdf)
    assert meta["page_count"] == 3
    assert meta["is_encrypted"] is False


def test_compute_sha256(synthetic_pdf: Path):
    """Verify SHA-256 calculation is deterministic and 64 hex characters."""
    hash1 = compute_sha256(synthetic_pdf)
    hash2 = compute_sha256(synthetic_pdf)
    assert hash1 == hash2
    assert len(hash1) == 64
    assert all(c in "0123456789abcdefABCDEF" for c in hash1)


def test_compute_sha256_missing_file(tmp_path: Path):
    """Verify FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(tmp_path / "nonexistent.pdf")


# --- Rendering Pipeline Tests ---

def test_deterministic_page_id_generation(synthetic_pdf: Path, tmp_path: Path):
    """Verify page IDs strictly follow {document_id}_p{page_num:04d} convention."""
    out_dir = tmp_path / "rendered_pages"
    manifest = render_pdf(
        pdf_path=synthetic_pdf,
        output_dir=out_dir,
        dpi=150,
        pages="1,3",
        document_id="test_doc",
    )

    assert len(manifest.pages) == 2
    assert manifest.pages[0].page_id == "test_doc_p0001"
    assert manifest.pages[0].page_number == 1
    assert manifest.pages[1].page_id == "test_doc_p0003"
    assert manifest.pages[1].page_number == 3


def test_render_pdf_dimensions_and_scaling(synthetic_pdf: Path, tmp_path: Path):
    """
    Verify resolution scaling matches DPI / 72.0.
    At 144 DPI on a 595x842 pt page, width ~ 595 * 2 = 1190, height ~ 842 * 2 = 1684.
    """
    out_dir = tmp_path / "scaled_pages"
    manifest = render_pdf(
        pdf_path=synthetic_pdf,
        output_dir=out_dir,
        dpi=144,
        pages="1",
        document_id="scaling_doc",
    )

    page_info = manifest.pages[0]
    expected_width = round(595.0 * (144.0 / 72.0))
    expected_height = round(842.0 * (144.0 / 72.0))

    # Allow 1-2 pixel margin due to MuPDF pixel boundary rounding
    assert abs(page_info.width - expected_width) <= 2
    assert abs(page_info.height - expected_height) <= 2
    assert page_info.dpi == 144

    # Verify PNG image actually exists on disk and is non-empty
    img_path = Path(page_info.image_path)
    assert img_path.is_file()
    assert img_path.stat().st_size > 1000


def test_provenance_manifest_emission(synthetic_pdf: Path, tmp_path: Path):
    """Verify page provenance manifest and unified document manifest are emitted correctly."""
    out_dir = tmp_path / "manifest_test"
    manifest = render_pdf(
        pdf_path=synthetic_pdf,
        output_dir=out_dir,
        dpi=300,
        pages="1-2",
        document_id="ambedkar_test",
    )

    # Check individual page manifests
    p1_manifest_file = out_dir / "ambedkar_test_p0001_manifest.json"
    assert p1_manifest_file.is_file()

    p1_prov = PageProvenance.from_json_file(p1_manifest_file)
    assert p1_prov.document_id == "ambedkar_test"
    assert p1_prov.page_id == "ambedkar_test_p0001"
    assert p1_prov.page_number == 1
    assert p1_prov.dpi == 300
    assert len(p1_prov.sha256) == 64
    assert p1_prov.source_pdf_sha256 == compute_sha256(synthetic_pdf)

    # Check unified document rendering manifest
    doc_manifest_file = out_dir / "ambedkar_test_rendered_manifest.json"
    assert doc_manifest_file.is_file()

    doc_manifest = DocumentRenderingManifest.from_json_file(doc_manifest_file)
    assert doc_manifest.document_id == "ambedkar_test"
    assert doc_manifest.total_pages_in_pdf == 3
    assert len(doc_manifest.pages) == 2


def test_duplicate_rendering_detection_caching(synthetic_pdf: Path, tmp_path: Path):
    """Verify idempotent rendering: skips re-rendering when image and manifest exist, unless force=True."""
    out_dir = tmp_path / "cache_test"

    # First run: renders page 1
    manifest_run1 = render_pdf(
        pdf_path=synthetic_pdf,
        output_dir=out_dir,
        dpi=300,
        pages="1",
        force=False,
        document_id="cache_doc",
    )
    assert manifest_run1.rendered_pages_count == 1
    assert manifest_run1.pages[0].status == "rendered"
    initial_sha = manifest_run1.pages[0].sha256

    # Second run without force: must be cached
    manifest_run2 = render_pdf(
        pdf_path=synthetic_pdf,
        output_dir=out_dir,
        dpi=300,
        pages="1",
        force=False,
        document_id="cache_doc",
    )
    assert manifest_run2.rendered_pages_count == 0
    assert manifest_run2.pages[0].status == "cached"
    assert manifest_run2.pages[0].sha256 == initial_sha

    # Third run with force=True: must re-render
    manifest_run3 = render_pdf(
        pdf_path=synthetic_pdf,
        output_dir=out_dir,
        dpi=300,
        pages="1",
        force=True,
        document_id="cache_doc",
    )
    assert manifest_run3.rendered_pages_count == 1
    assert manifest_run3.pages[0].status == "rendered"


def test_render_pdf_dpi_validation(synthetic_pdf: Path, tmp_path: Path):
    """Verify invalid DPI values raise ValueError."""
    with pytest.raises(ValueError, match="DPI must be between"):
        render_pdf(synthetic_pdf, tmp_path, dpi=50)

    with pytest.raises(ValueError, match="DPI must be between"):
        render_pdf(synthetic_pdf, tmp_path, dpi=2400)


def test_render_pdf_from_manifest_json(synthetic_pdf: Path, tmp_path: Path):
    """Verify render_pdf can ingest a DocumentManifest JSON file."""
    manifest_file = tmp_path / "intake_manifest.json"
    manifest_data = {
        "document_id": "ingested_manifest_doc",
        "title": "Test Manifest Intake",
        "source_organization": "National Archives",
        "language": "eng",
        "script": "Latn",
        "rights_status": "public",
        "rights_evidence": "Statutory public domain",
        "local_path": str(synthetic_pdf),
        "page_count": 3,
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    out_dir = tmp_path / "rendered_from_manifest"
    result = render_pdf(
        pdf_path=manifest_file,
        output_dir=out_dir,
        dpi=150,
        pages="1",
    )
    assert result.document_id == "ingested_manifest_doc"
    assert result.pages[0].page_id == "ingested_manifest_doc_p0001"


# --- CLI Integration Tests ---

def test_cli_render_pdf_help():
    """Verify render_pdf.py CLI --help executes cleanly with code 0."""
    with pytest.raises(SystemExit) as exc:
        cli_main(["--help"])
    assert exc.value.code == 0


def test_cli_render_pdf_execution(synthetic_pdf: Path, tmp_path: Path):
    """Verify render_pdf.py CLI renders pages and returns code 0."""
    out_dir = tmp_path / "cli_out"
    exit_code = cli_main([
        "-i", str(synthetic_pdf),
        "-o", str(out_dir),
        "-d", "150",
        "-p", "1-2",
        "--document-id", "cli_test_doc",
    ])
    assert exit_code == 0
    assert (out_dir / "cli_test_doc_p0001.png").is_file()
    assert (out_dir / "cli_test_doc_p0002.png").is_file()


def test_cli_render_pdf_missing_file(tmp_path: Path):
    """Verify render_pdf.py CLI handles missing file with exit code 1."""
    exit_code = cli_main([
        "-i", str(tmp_path / "nonexistent.pdf"),
    ])
    assert exit_code == 1
