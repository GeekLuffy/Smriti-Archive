"""
Tests for all Pydantic v2 schemas across the sih_archive framework.
Covers DocumentManifest, PageProvenance, DocumentRenderingManifest,
TokenRegion, ProcessingMetadata, OCROutput, GroundTruthPage,
EditOperationBreakdown, BoundingBoxMetrics, PageMetrics, and SummaryMetrics.
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from sih_archive.schemas.manifest import DocumentManifest, RightsStatus
from sih_archive.schemas.rendering import DocumentRenderingManifest, PageProvenance
from sih_archive.schemas.ocr import (
    OCROutput,
    OCRStatus,
    ProcessingMetadata,
    RegionType,
    TokenRegion,
)
from sih_archive.schemas.evaluation import (
    BoundingBoxMetrics,
    EditOperationBreakdown,
    EvaluationStatus,
    GroundTruthPage,
    GroundTruthRegion,
    PageMetrics,
    SummaryMetrics,
)


# ==============================================================================
# 1. Manifest Schemas
# ==============================================================================

def test_document_manifest_valid():
    manifest = DocumentManifest(
        document_id="ambedkar_speech_vol1",
        title="Speeches of Dr. Ambedkar",
        source_url="https://example.org/archive",
        source_organization="Archives of India",
        language="eng",
        script="Latn",
        rights_status="public",
        rights_evidence="Govt publication expired under Section 22",
        local_path="data/raw/ambedkar_speech_vol1.pdf",
        page_count=5,
        notes="Volume 1 digitized",
    )
    assert manifest.document_id == "ambedkar_speech_vol1"
    assert manifest.language == "eng"
    assert manifest.script == "Latn"
    assert manifest.rights_status == "public"


def test_document_manifest_invalid_document_id():
    with pytest.raises(ValidationError):
        DocumentManifest(
            document_id="bad/path/traversal",
            title="Invalid",
            source_organization="Test Org",
            language="eng",
            script="Latn",
            rights_status="unknown",
            local_path="data/raw/doc.pdf",
            page_count=1,
        )


def test_document_manifest_requires_evidence_for_public_and_verified():
    with pytest.raises(ValidationError) as exc:
        DocumentManifest(
            document_id="doc1",
            title="Public Doc Without Evidence",
            source_organization="Test Org",
            language="eng",
            script="Latn",
            rights_status="public",
            rights_evidence=None,
            local_path="data/raw/doc.pdf",
            page_count=1,
        )
    assert "rights_evidence" in str(exc.value)


def test_document_manifest_json_roundtrip(tmp_path):
    manifest = DocumentManifest(
        document_id="test_doc_001",
        title="Test Doc",
        source_organization="Test Org",
        language="mar",
        script="Deva",
        rights_status="unknown",
        local_path="data/raw/test.pdf",
        page_count=2,
    )
    json_path = tmp_path / "manifest.json"
    manifest.to_json_file(json_path)
    loaded = DocumentManifest.from_json_file(json_path)
    assert loaded.document_id == manifest.document_id
    assert loaded.language == "mar"
    assert loaded.script == "Deva"


# ==============================================================================
# 2. Rendering Schemas
# ==============================================================================

def test_page_provenance_valid():
    valid_sha256 = "a" * 64
    prov = PageProvenance(
        document_id="doc1",
        page_id="doc1_p0001",
        page_number=1,
        width=2480,
        height=3509,
        orig_width_pt=595.0,
        orig_height_pt=842.0,
        rotation=0,
        dpi=300,
        source_pdf="data/raw/doc1.pdf",
        source_pdf_sha256=valid_sha256,
        image_path="data/processed/pages/doc1_p0001.png",
        sha256=valid_sha256,
        status="rendered",
    )
    assert prov.page_id == "doc1_p0001"
    assert prov.dpi == 300
    assert prov.status == "rendered"


def test_page_provenance_invalid_page_id():
    valid_sha256 = "a" * 64
    with pytest.raises(ValidationError):
        PageProvenance(
            document_id="doc1",
            page_id="invalid_page_name",
            page_number=1,
            width=2480,
            height=3509,
            orig_width_pt=595.0,
            orig_height_pt=842.0,
            dpi=300,
            source_pdf="data/raw/doc1.pdf",
            source_pdf_sha256=valid_sha256,
            image_path="page.png",
            sha256=valid_sha256,
        )


def test_document_rendering_manifest_roundtrip(tmp_path):
    valid_sha256 = "b" * 64
    prov = PageProvenance(
        document_id="doc1",
        page_id="doc1_p0001",
        page_number=1,
        width=2480,
        height=3509,
        orig_width_pt=595.0,
        orig_height_pt=842.0,
        dpi=300,
        source_pdf="data/raw/doc1.pdf",
        source_pdf_sha256=valid_sha256,
        image_path="data/processed/pages/doc1_p0001.png",
        sha256=valid_sha256,
    )
    doc_manifest = DocumentRenderingManifest(
        document_id="doc1",
        source_pdf="data/raw/doc1.pdf",
        source_pdf_sha256="hash1",
        dpi=300,
        total_pages_in_pdf=1,
        rendered_pages_count=1,
        pages=[prov],
    )
    json_path = tmp_path / "rendering_manifest.json"
    doc_manifest.to_json_file(json_path)
    loaded = DocumentRenderingManifest.from_json_file(json_path)
    assert loaded.document_id == "doc1"
    assert len(loaded.pages) == 1
    assert loaded.pages[0].page_id == "doc1_p0001"


# ==============================================================================
# 3. OCR Schemas
# ==============================================================================

def test_token_region_valid():
    region = TokenRegion(
        type="word",
        text="Babasaheb",
        bbox=[100, 200, 150, 40],
        confidence=98.5,
        block_num=1,
        line_num=1,
        word_num=1,
    )
    assert region.text == "Babasaheb"
    assert region.confidence == 98.5
    assert region.bbox == [100, 200, 150, 40]


def test_token_region_invalid_bbox_coordinates():
    with pytest.raises(ValidationError):
        # Negative coordinate
        TokenRegion(type="word", text="test", bbox=[-5, 10, 20, 20], confidence=90.0)


def test_token_region_confidence_out_of_bounds():
    with pytest.raises(ValidationError):
        TokenRegion(type="word", text="test", bbox=[0, 0, 10, 10], confidence=105.0)


def test_ocr_output_schema_roundtrip(tmp_path):
    ocr_out = OCROutput(
        document_id="doc1",
        page_id="doc1_p0001",
        language="eng",
        engine="mock",
        engine_version="1.0.0",
        image_path="page.png",
        processing=ProcessingMetadata(dpi=300, filters=["grayscale", "clahe"], duration_ms=25.5),
        text="SPEECHES OF DR. AMBEDKAR",
        regions=[
            TokenRegion(type="word", text="SPEECHES", bbox=[10, 10, 100, 30], confidence=99.0),
            TokenRegion(type="word", text="OF", bbox=[120, 10, 30, 30], confidence=99.0),
        ],
        status="success",
    )
    json_path = tmp_path / "ocr_output.json"
    ocr_out.to_json_file(json_path)
    loaded = OCROutput.from_json_file(json_path)
    assert loaded.document_id == "doc1"
    assert loaded.processing.filters == ["grayscale", "clahe"]
    assert len(loaded.regions) == 2


# ==============================================================================
# 4. Evaluation Schemas
# ==============================================================================

def test_ground_truth_page_roundtrip(tmp_path):
    gt = GroundTruthPage(
        document_id="doc1",
        page_id="doc1_p0001",
        reference_text="ANNIHILATION OF CASTE",
        language="eng",
        script="Latn",
        annotator="Archivist 1",
        verification_status="verified",
        regions=[
            GroundTruthRegion(region_id="r1", type="word", text="ANNIHILATION", bbox=[10, 20, 150, 40]),
            GroundTruthRegion(region_id="r2", type="word", text="OF", bbox=[170, 20, 40, 40]),
            GroundTruthRegion(region_id="r3", type="word", text="CASTE", bbox=[220, 20, 100, 40]),
        ],
    )
    json_path = tmp_path / "gt.json"
    gt.to_json_file(json_path)
    loaded = GroundTruthPage.from_json_file(json_path)
    assert loaded.page_id == "doc1_p0001"
    assert len(loaded.regions) == 3


def test_edit_operation_breakdown():
    breakdown = EditOperationBreakdown(
        substitutions=2,
        deletions=1,
        insertions=1,
        reference_length=20,
        hypothesis_length=20,
        total_distance=4,
        error_rate=0.20,
    )
    assert breakdown.total_distance == 4
    assert breakdown.error_rate == 0.20


def test_bounding_box_metrics():
    bbox = BoundingBoxMetrics(
        total_hypothesis_boxes=10,
        total_reference_boxes=10,
        true_positives=9,
        false_positives=1,
        false_negatives=1,
        precision=0.9,
        recall=0.9,
        f1=0.9,
        mean_iou=0.85,
        iou_threshold=0.5,
        matched_pairs_count=9,
    )
    assert bbox.f1 == 0.9
    assert bbox.mean_iou == 0.85


def test_page_metrics_unavailable_factory():
    pm = PageMetrics.create_unavailable(
        document_id="doc1",
        page_id="doc1_p0002",
        engine="mock",
        pipeline="raw",
    )
    assert pm.status == "ground_truth_unavailable"
    assert pm.cer is None
    assert pm.wer is None
    assert pm.bbox_metrics is None
    assert pm.reading_order_score is None


def test_summary_metrics_json_and_csv_export(tmp_path):
    pm1 = PageMetrics(
        document_id="doc1",
        page_id="doc1_p0001",
        engine="mock",
        pipeline="raw",
        status="evaluated",
        cer=0.05,
        wer=0.10,
        cer_breakdown=EditOperationBreakdown(
            substitutions=1, deletions=0, insertions=0,
            reference_length=20, hypothesis_length=20,
            total_distance=1, error_rate=0.05
        ),
        bbox_metrics=BoundingBoxMetrics(
            total_hypothesis_boxes=5, total_reference_boxes=5,
            true_positives=5, false_positives=0, false_negatives=0,
            precision=1.0, recall=1.0, f1=1.0, mean_iou=0.9,
            iou_threshold=0.5, matched_pairs_count=5
        ),
        reading_order_score=1.0,
    )
    pm2 = PageMetrics.create_unavailable("doc1", "doc1_p0002", engine="mock", pipeline="raw")

    summary = SummaryMetrics(
        total_pages=2,
        evaluated_pages=1,
        unavailable_pages=1,
        error_pages=0,
        mean_cer=0.05,
        mean_wer=0.10,
        mean_precision=1.0,
        mean_recall=1.0,
        mean_f1=1.0,
        mean_iou=0.9,
        mean_reading_order_score=1.0,
        page_metrics=[pm1, pm2],
    )

    json_file = tmp_path / "summary.json"
    csv_file = tmp_path / "summary.csv"

    summary.to_json_file(json_file)
    summary.to_csv_file(csv_file)

    assert json_file.is_file()
    assert csv_file.is_file()

    loaded = SummaryMetrics.from_json_file(json_file)
    assert loaded.total_pages == 2
    assert loaded.evaluated_pages == 1
    assert loaded.unavailable_pages == 1

    with open(csv_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "doc1_p0001" in content
    assert "doc1_p0002" in content
    assert "ground_truth_unavailable" in content
