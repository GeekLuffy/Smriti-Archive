"""Comprehensive unit test suite for Milestone 1 & 2:
- Architecture & PyMuPDF verification
- DocumentManifest schema validation (Pydantic v2)
- Ingestion protocol, rights hygiene, and intake auditing
"""

import hashlib
from pathlib import Path
import tempfile
import pytest
from pydantic import ValidationError

import pymupdf as fitz
import fitz as legacy_fitz
from sih_archive.schemas.manifest import DocumentManifest, RightsStatus
from sih_archive.ingestion.protocol import (
    IngestionError,
    RightsHygieneError,
    audit_intake,
    check_rights_hygiene,
    create_manifest,
    discover_manifests,
    load_manifest,
    save_manifest,
    validate_manifest,
    validate_raw_file_location,
)


# --- Milestone 1 Verification Tests ---

def test_pymupdf_installed_and_functional():
    """Verify PyMuPDF is installed, imports as fitz, and can create/render a page."""
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((20, 50), "Test PyMuPDF Rendering", fontsize=14)
    pix = page.get_pixmap(dpi=150)
    assert pix.width > 0
    assert pix.height > 0
    doc.close()


def test_package_structure_and_imports():
    """Verify all sih_archive packages are importable."""
    import sih_archive
    import sih_archive.schemas
    import sih_archive.ingestion
    import sih_archive.rendering
    import sih_archive.ocr
    import sih_archive.preprocessing
    import sih_archive.evaluation
    import sih_archive.utils

    assert sih_archive.__version__ == "0.1.0"


# --- Milestone 2: DocumentManifest Schema Tests ---

def test_valid_manifest_creation():
    """Test valid DocumentManifest instantiation with all required fields."""
    manifest = DocumentManifest(
        document_id="doc_test_001",
        title="Historical Gazette Volume 1",
        source_url="https://archives.gov.in/doc1",
        source_organization="National Archives of India",
        language="eng",
        script="Latn",
        rights_status="public",
        rights_evidence="Indian Copyright Act 1957 Section 52(1)(q)",
        local_path="data/raw/gazette_vol1.pdf",
        page_count=120,
        notes="Clean photostat copy.",
        checksum_sha256="a" * 64,
    )
    assert manifest.document_id == "doc_test_001"
    assert manifest.page_count == 120
    assert manifest.rights_status == "public"
    assert manifest.checksum_sha256 == "a" * 64


def test_manifest_path_traversal_rejection_in_document_id():
    """Test rejection of path traversal characters in document_id."""
    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="../malicious_id",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/test.pdf",
            page_count=10,
        )

    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="sub/dir/id",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/test.pdf",
            page_count=10,
        )


def test_manifest_local_path_constraints():
    """Test that local_path must be within data/raw/ and reject directory traversal."""
    # Outside data/raw/
    with pytest.raises(ValidationError) as exc:
        DocumentManifest(
            document_id="doc_outside",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="unknown",
            local_path="data/processed/test.pdf",
            page_count=10,
        )
    assert "must reside within 'data/raw/'" in str(exc.value)

    # Path traversal in local_path
    with pytest.raises(ValidationError) as exc:
        DocumentManifest(
            document_id="doc_traversal",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/../../etc/passwd",
            page_count=10,
        )
    assert "directory traversal" in str(exc.value)


def test_manifest_language_and_script_patterns():
    """Test ISO 639-3 language and ISO 15924 script pattern validations."""
    # Invalid language (2 letters instead of 3)
    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="doc_bad_lang",
            title="Test Doc",
            source_organization="Org",
            language="en",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/test.pdf",
            page_count=10,
        )

    # Invalid language (uppercase)
    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="doc_bad_lang2",
            title="Test Doc",
            source_organization="Org",
            language="ENG",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/test.pdf",
            page_count=10,
        )

    # Invalid script (all lowercase)
    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="doc_bad_script",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="latn",
            rights_status="unknown",
            local_path="data/raw/test.pdf",
            page_count=10,
        )


def test_manifest_page_count_validation():
    """Test that page_count must be >= 1."""
    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="doc_zero_pages",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/test.pdf",
            page_count=0,
        )

    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="doc_neg_pages",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/test.pdf",
            page_count=-5,
        )


def test_manifest_rights_evidence_enforcement():
    """Test that 'public' and 'verified' require non-empty rights_evidence, while 'unknown' does not."""
    # Public without evidence must fail
    with pytest.raises(ValidationError) as exc:
        DocumentManifest(
            document_id="doc_public_no_ev",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="public",
            rights_evidence=None,
            local_path="data/raw/test.pdf",
            page_count=10,
        )
    assert "must include non-empty 'rights_evidence'" in str(exc.value)

    # Verified without evidence must fail
    with pytest.raises(ValidationError) as exc:
        DocumentManifest(
            document_id="doc_verified_no_ev",
            title="Test Doc",
            source_organization="Org",
            language="eng",
            script="Latn",
            rights_status="verified",
            rights_evidence="",
            local_path="data/raw/test.pdf",
            page_count=10,
        )
    assert "must include non-empty 'rights_evidence'" in str(exc.value)

    # Unknown without evidence is permitted
    doc_unknown = DocumentManifest(
        document_id="doc_unknown",
        title="Test Doc",
        source_organization="Org",
        language="eng",
        script="Latn",
        rights_status="unknown",
        rights_evidence=None,
        local_path="data/raw/test.pdf",
        page_count=10,
    )
    assert doc_unknown.rights_status == "unknown"


def test_manifest_json_serialization_roundtrip(tmp_path):
    """Test JSON serialization and deserialization preserves all fields accurately."""
    manifest = DocumentManifest(
        document_id="ambedkar_vol_roundtrip",
        title="Writings & Speeches",
        source_url="https://example.org/ambedkar",
        source_organization="Dr. Ambedkar Foundation",
        language="mar",
        script="Deva",
        rights_status="public",
        rights_evidence="Section 22 Copyright Expiry (60 years post-mortem)",
        local_path="data/raw/ambedkar_mar.pdf",
        page_count=350,
        notes="Marathi edition text.",
        checksum_sha256="c" * 64,
    )
    json_file = tmp_path / "ambedkar_vol_roundtrip.json"
    manifest.to_json_file(json_file)
    assert json_file.is_file()

    loaded = DocumentManifest.from_json_file(json_file)
    assert loaded.document_id == manifest.document_id
    assert loaded.title == manifest.title
    assert loaded.language == "mar"
    assert loaded.script == "Deva"
    assert loaded.checksum_sha256 == "c" * 64


def test_manifest_checksum_and_integrity_verification(tmp_path):
    """Test genuine SHA-256 calculation and verification on a physical file."""
    # Create fake repo root structure
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    test_file = raw_dir / "sample.pdf"
    content = b"PDF-1.7 genuine test archival document stream"
    test_file.write_bytes(content)
    expected_hash = hashlib.sha256(content).hexdigest()

    manifest = DocumentManifest(
        document_id="doc_hash_test",
        title="Hash Test Doc",
        source_organization="Test Org",
        language="eng",
        script="Latn",
        rights_status="restricted",
        rights_evidence="Fair dealing test",
        local_path="data/raw/sample.pdf",
        page_count=1,
        checksum_sha256=expected_hash,
    )

    computed = manifest.compute_sha256(repo_root=tmp_path)
    assert computed == expected_hash
    assert manifest.verify_integrity(repo_root=tmp_path) is True

    # Tamper with file
    test_file.write_bytes(b"tampered content")
    assert manifest.verify_integrity(repo_root=tmp_path) is False


# --- Ingestion Protocol Function Tests ---

def test_validate_raw_file_location():
    """Test raw file location validation and escape rejection."""
    # Valid relative path
    p = validate_raw_file_location("data/raw/valid.pdf", repo_root=".")
    assert p.name == "valid.pdf"

    # Attempted traversal out of raw
    with pytest.raises(IngestionError):
        validate_raw_file_location("data/processed/pages/bad.png", repo_root=".")


def test_check_rights_hygiene():
    """Test rights hygiene evaluation for all four statuses."""
    # Public
    m_pub = DocumentManifest(
        document_id="doc_pub",
        title="Pub Doc",
        source_organization="Org",
        language="eng",
        script="Latn",
        rights_status="public",
        rights_evidence="Indian Copyright Act Section 52(1)(q)",
        local_path="data/raw/pub.pdf",
        page_count=5,
    )
    res_pub = check_rights_hygiene(m_pub)
    assert res_pub["cleared_for_benchmark"] is True
    assert res_pub["allows_redistribution"] is True
    assert res_pub["requires_rights_audit"] is False

    # Verified
    m_ver = DocumentManifest(
        document_id="doc_ver",
        title="Ver Doc",
        source_organization="Org",
        language="eng",
        script="Latn",
        rights_status="verified",
        rights_evidence="Custodial CC-BY-NC 4.0",
        local_path="data/raw/ver.pdf",
        page_count=5,
    )
    res_ver = check_rights_hygiene(m_ver)
    assert res_ver["cleared_for_benchmark"] is True
    assert res_ver["allows_redistribution"] is False

    # Restricted
    m_res = DocumentManifest(
        document_id="doc_res",
        title="Res Doc",
        source_organization="Org",
        language="eng",
        script="Latn",
        rights_status="restricted",
        rights_evidence="Fair dealing benchmarking",
        local_path="data/raw/res.pdf",
        page_count=5,
    )
    res_res = check_rights_hygiene(m_res)
    assert res_res["cleared_for_benchmark"] is True
    assert res_res["allows_redistribution"] is False
    assert res_res["requires_rights_audit"] is True

    # Unknown
    m_unk = DocumentManifest(
        document_id="doc_unk",
        title="Unk Doc",
        source_organization="Org",
        language="eng",
        script="Latn",
        rights_status="unknown",
        local_path="data/raw/unk.pdf",
        page_count=5,
    )
    res_unk = check_rights_hygiene(m_unk)
    assert res_unk["cleared_for_benchmark"] is False
    assert res_unk["requires_rights_audit"] is True


def test_create_and_save_manifest(tmp_path):
    """Test create_manifest helper and auto-computation of checksum."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    pdf_path = raw_dir / "sample_doc.pdf"
    pdf_path.write_bytes(b"Simulated PDF content for create_manifest test")
    expected_sha = hashlib.sha256(b"Simulated PDF content for create_manifest test").hexdigest()

    manifest = create_manifest(
        document_id="sample_doc_01",
        title="Sample Archive Document",
        source_organization="State Archives",
        language="hin",
        script="Deva",
        rights_status="public",
        rights_evidence="Official Gazette publication",
        local_path="data/raw/sample_doc.pdf",
        page_count=12,
        repo_root=tmp_path,
        auto_compute_checksum=True,
    )
    assert manifest.checksum_sha256 == expected_sha

    m_dir = tmp_path / "data" / "manifests"
    saved_path = save_manifest(manifest, output_dir=m_dir)
    assert saved_path.is_file()
    assert saved_path.name == "sample_doc_01.json"

    reloaded = load_manifest(saved_path)
    assert reloaded.document_id == "sample_doc_01"
    assert reloaded.language == "hin"
    assert reloaded.script == "Deva"


def test_validate_manifest_and_audit_intake(tmp_path):
    """Test intake auditing, missing file detection, and unmanifested asset discovery."""
    raw_dir = tmp_path / "data" / "raw"
    m_dir = tmp_path / "data" / "manifests"
    raw_dir.mkdir(parents=True)
    m_dir.mkdir(parents=True)

    # 1. Manifest with existing valid file
    file1 = raw_dir / "doc1.pdf"
    file1.write_bytes(b"Doc 1 content")
    m1 = create_manifest(
        document_id="doc1",
        title="Document One",
        source_organization="Org 1",
        language="eng",
        script="Latn",
        rights_status="public",
        rights_evidence="Public law 101",
        local_path="data/raw/doc1.pdf",
        page_count=2,
        repo_root=tmp_path,
    )
    save_manifest(m1, m_dir)

    # 2. Manifest with MISSING physical file
    m2 = DocumentManifest(
        document_id="doc2_missing",
        title="Document Two",
        source_organization="Org 2",
        language="eng",
        script="Latn",
        rights_status="unknown",
        local_path="data/raw/doc2_missing.pdf",
        page_count=5,
    )
    save_manifest(m2, m_dir)

    # 3. Unmanifested raw file in data/raw/
    unman_file = raw_dir / "unmanifested_extra.pdf"
    unman_file.write_bytes(b"Unmanifested rogue asset")

    # Audit intake
    audit = audit_intake(repo_root=tmp_path, manifest_dir=m_dir, raw_dir=raw_dir)
    assert audit["total_manifests"] == 2
    assert audit["total_raw_files"] == 2  # doc1.pdf + unmanifested_extra.pdf
    assert len(audit["missing_raw_files"]) == 1
    assert audit["missing_raw_files"][0]["document_id"] == "doc2_missing"
    assert "data/raw/unmanifested_extra.pdf" in audit["unmanifested_raw_files"]
    assert audit["hygiene_compliance"] is False  # unmanifested asset present


def test_verified_sample_manifest_in_repository():
    """Verify the repository's sample manifest data/manifests/ambedkar_speech_vol1.json."""
    manifest_path = Path("data/manifests/ambedkar_speech_vol1.json")
    assert manifest_path.is_file(), "data/manifests/ambedkar_speech_vol1.json must exist."

    manifest = load_manifest(manifest_path)
    assert manifest.document_id == "ambedkar_speech_vol1"
    assert manifest.language == "eng"
    assert manifest.script == "Latn"
    assert manifest.rights_status == "public"
    assert manifest.rights_evidence is not None and len(manifest.rights_evidence) > 0
    assert manifest.local_path == "data/raw/ambedkar_speech_vol1.pdf"
    assert manifest.page_count == 5

    # Check validation against repository root
    val = validate_manifest(manifest, repo_root=".")
    assert val["is_valid"] is True
    assert val["raw_file_exists"] is True
    assert val["checksum_valid"] is True
    assert val["ready_for_processing"] is True
    assert len(val["issues"]) == 0
