"""
Unit and Integration Tests for scripts/ingest.py and scripts/run_benchmarks.py (SIH26096 Tasks 1, 6).
"""

import json
from pathlib import Path
import subprocess
import sys
from PIL import Image
import pymupdf
import pytest

# Ensure scripts and src are accessible
repo_root = Path(__file__).resolve().parent.parent
scripts_dir = repo_root / "scripts"
src_dir = repo_root / "src"
for d in (scripts_dir, src_dir):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

import ingest
import run_benchmarks
from sih_archive.schemas.evaluation import GroundTruthPage
from sih_archive.schemas.manifest import DocumentManifest


@pytest.fixture
def synthetic_pdf(tmp_path):
    """Creates a minimal valid single-page PDF."""
    pdf_path = tmp_path / "test_doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=400)
    page.insert_text((50, 50), "Test archival content for ingestion.")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def synthetic_image(tmp_path):
    """Creates a minimal valid single-page image."""
    img_path = tmp_path / "test_page.png"
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    img.save(img_path)
    return img_path


def test_cli_ingest_help():
    """Verify scripts/ingest.py --help returns code 0 and displays CLI usage."""
    cmd = [sys.executable, str(scripts_dir / "ingest.py"), "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Archival Document Ingestion & Rights Intake CLI" in res.stdout
    assert "--document-id" in res.stdout


def test_cli_ingest_missing_file():
    """Verify ingest fails gracefully when the input file does not exist."""
    ret = ingest.main([
        "--file", "nonexistent_file_xyz.pdf",
        "--document-id", "test_fail",
        "--title", "Nonexistent",
        "--source-organization", "National Archives",
        "--rights-status", "public",
        "--rights-evidence", "Indian Copyright Act 1957 Section 52(1)(q)",
    ])
    assert ret == 1


def test_cli_ingest_missing_rights_evidence_for_public(synthetic_pdf):
    """Verify rights hygiene rejects public/verified intake without statutory evidence."""
    ret = ingest.main([
        "--file", str(synthetic_pdf),
        "--document-id", "test_no_evidence",
        "--title", "Test Title",
        "--source-organization", "National Archives",
        "--rights-status", "public",
    ])
    assert ret == 1


def test_cli_ingest_valid_pdf_and_manifest(synthetic_pdf, monkeypatch, tmp_path):
    """Verify successful ingestion of a PDF document into repo data directories."""
    # Monkeypatch repo_root to tmp_path to isolate filesystem side-effects
    monkeypatch.setattr(ingest, "repo_root", tmp_path)

    ret = ingest.main([
        "--file", str(synthetic_pdf),
        "--document-id", "doc_test_001",
        "--title", "Archival Volume 1",
        "--source-organization", "Archaeological Survey of India",
        "--source-url", "https://asi.nic.in/archive/doc1",
        "--language", "eng",
        "--script", "Latn",
        "--rights-status", "public",
        "--rights-evidence", "Indian Copyright Act 1957 Section 52(1)(q)",
        "--notes", "Test sample for unit test suite",
    ])
    assert ret == 0

    dest_file = tmp_path / "data" / "raw" / "doc_test_001.pdf"
    manifest_file = tmp_path / "data" / "manifests" / "doc_test_001.json"

    assert dest_file.is_file()
    assert manifest_file.is_file()

    manifest = DocumentManifest.from_json_file(manifest_file)
    assert manifest.document_id == "doc_test_001"
    assert manifest.page_count == 1
    assert manifest.rights_status == "public"
    assert manifest.rights_evidence == "Indian Copyright Act 1957 Section 52(1)(q)"


def test_cli_ingest_image_with_text_ground_truth(synthetic_image, monkeypatch, tmp_path):
    """Verify ingestion of a page image along with a plain-text ground-truth file."""
    monkeypatch.setattr(ingest, "repo_root", tmp_path)

    gt_txt = tmp_path / "transcript.txt"
    gt_txt.write_text("Reference transcript text line 1\nLine 2.", encoding="utf-8")

    ret = ingest.main([
        "--file", str(synthetic_image),
        "--document-id", "img_doc_002",
        "--title", "Single Leaf Manuscript",
        "--source-organization", "State Archives",
        "--language", "hin",
        "--rights-status", "verified",
        "--rights-evidence", "Custodial clearance reference ASI/2026/09",
        "--ground-truth", str(gt_txt),
    ])
    assert ret == 0

    gt_json = tmp_path / "data" / "ground_truth" / "img_doc_002_p0001.json"
    assert gt_json.is_file()

    gt_obj = GroundTruthPage.from_json_file(gt_json)
    assert gt_obj.document_id == "img_doc_002"
    assert gt_obj.page_id == "img_doc_002_p0001"
    assert "Reference transcript text" in gt_obj.reference_text
    assert gt_obj.language == "hin"
    assert gt_obj.script == "Deva"


def test_cli_ingest_with_json_ground_truth(synthetic_pdf, monkeypatch, tmp_path):
    """Verify ingestion with a pre-formatted GroundTruthPage JSON file."""
    monkeypatch.setattr(ingest, "repo_root", tmp_path)

    gt_data = {
        "document_id": "json_gt_doc",
        "page_id": "json_gt_doc_p0001",
        "reference_text": "Verified structured transcript.",
        "language": "eng",
        "script": "Latn",
        "annotator": "Senior Paleographer",
        "verification_status": "verified",
        "regions": [],
    }
    gt_file = tmp_path / "gt_source.json"
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(gt_data, f)

    ret = ingest.main([
        "--file", str(synthetic_pdf),
        "--document-id", "json_gt_doc",
        "--title", "JSON GT Doc",
        "--source-organization", "National Museum",
        "--rights-status", "public",
        "--rights-evidence", "Crown Copyright expired",
        "--ground-truth", str(gt_file),
    ])
    assert ret == 0

    gt_dest = tmp_path / "data" / "ground_truth" / "json_gt_doc_p0001.json"
    assert gt_dest.is_file()
    gt_obj = GroundTruthPage.from_json_file(gt_dest)
    assert gt_obj.annotator == "Senior Paleographer"


def test_cli_ingest_malformed_json_ground_truth(synthetic_pdf, monkeypatch, tmp_path):
    """Verify ingestion fails when the provided ground-truth JSON is malformed."""
    monkeypatch.setattr(ingest, "repo_root", tmp_path)

    bad_gt_file = tmp_path / "bad_gt.json"
    bad_gt_file.write_text("{invalid json format: missing quotes}", encoding="utf-8")

    ret = ingest.main([
        "--file", str(synthetic_pdf),
        "--document-id", "bad_gt_doc",
        "--title", "Bad GT Doc",
        "--source-organization", "National Museum",
        "--rights-status", "public",
        "--rights-evidence", "Indian Copyright Act 1957 Section 52(1)(q)",
        "--ground-truth", str(bad_gt_file),
    ])
    assert ret == 1


def test_cli_run_benchmarks_help():
    """Verify scripts/run_benchmarks.py --help returns code 0."""
    cmd = [sys.executable, str(scripts_dir / "run_benchmarks.py"), "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "--output-dir" in res.stdout


def test_cli_run_benchmarks_execution(tmp_path):
    """Verify scripts/run_benchmarks.py compiles E1, E2, and E3 machine-readable results."""
    ret = run_benchmarks.main(["--output-dir", str(tmp_path)])
    assert ret == 0

    e1_file = tmp_path / "e1_ocr_results.json"
    e2_file = tmp_path / "e2_retrieval_results.json"
    e3_file = tmp_path / "e3_attribution_results.json"

    assert e1_file.is_file()
    assert e2_file.is_file()
    assert e3_file.is_file()

    # Verify E1 structure
    with open(e1_file, "r", encoding="utf-8") as f:
        e1_data = json.load(f)
    assert e1_data["phase"] == "E1_OCR"
    assert "gate_status" in e1_data
    assert "research_integrity_notice" in e1_data
    assert "metrics_definition" in e1_data

    # Verify E2 structure
    with open(e2_file, "r", encoding="utf-8") as f:
        e2_data = json.load(f)
    assert e2_data["phase"] == "E2_RETRIEVAL"
    assert "LOCKED" in e2_data["gate_status"]
    assert "gating_rule" in e2_data
    assert len(e2_data["engine_benchmarks"]) > 0

    # Verify E3 structure
    with open(e3_file, "r", encoding="utf-8") as f:
        e3_data = json.load(f)
    assert e3_data["phase"] == "E3_ATTRIBUTION"
    assert "LOCKED" in e3_data["gate_status"]
    assert "attribution_chain" in e3_data
    assert len(e3_data["answers"]) > 0
