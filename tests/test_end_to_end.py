"""
End-to-End Synthetic Benchmark Pipeline Integration Test (SIH26096 Requirement R7).

Executes the complete pipeline entirely offline using synthetic in-memory/disk fixtures:
1. Synthesizes an authentic multi-page PDF using PyMuPDF.
2. Renders pages deterministically at 300 DPI with cryptographic provenance manifests.
3. Applies modular image preprocessing filters (grayscale, CLAHE).
4. Executes OCR using the MockOCRAdapter preserving token regions and confidence scores.
5. Evaluates hypothesis against verified ground truth (with partial ground truth testing).
6. Generates publication-grade Markdown, JSON, CSV reports and Matplotlib charts.
"""

from pathlib import Path
import sys
import fitz  # PyMuPDF
import pytest

# Ensure scripts and src are accessible
repo_root = Path(__file__).resolve().parent.parent
scripts_dir = repo_root / "scripts"
src_dir = repo_root / "src"
for d in (scripts_dir, src_dir):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from sih_archive.rendering.pdf import render_pdf
from sih_archive.preprocessing.filters import PreprocessingPipeline
from sih_archive.ocr.mock import MockOCRAdapter
from sih_archive.schemas.ocr import OCROutput
from sih_archive.schemas.evaluation import GroundTruthPage, GroundTruthRegion, SummaryMetrics
import evaluate_ocr
import generate_report


@pytest.fixture
def synthetic_pdf(tmp_path) -> Path:
    """Creates a 2-page synthetic archival PDF document using PyMuPDF."""
    pdf_path = tmp_path / "synthetic_archive_vol1.pdf"
    doc = fitz.open()

    # Page 1: Title page
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text(
        (72, 100),
        "HISTORICAL PAPERS AND SPEECHES OF DR. BABASAHEB AMBEDKAR",
        fontsize=16,
    )
    p1.insert_text(
        (72, 140),
        "VOLUME I: CASTES IN INDIA MECHANISM GENESIS AND DEVELOPMENT",
        fontsize=12,
    )

    # Page 2: Text page
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(
        (72, 100),
        "ANNIHILATION OF CASTE WITH A REPLY TO MAHATMA GANDHI",
        fontsize=14,
    )

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_complete_synthetic_end_to_end_pipeline(synthetic_pdf, tmp_path):
    """
    Executes all benchmark phases end-to-end and validates artifacts.
    """
    work_dir = tmp_path / "pipeline_run"
    pages_dir = work_dir / "pages"
    preprocessed_dir = work_dir / "preprocessed"
    ocr_dir = work_dir / "ocr"
    gt_dir = work_dir / "ground_truth"
    metrics_dir = work_dir / "metrics"
    reports_dir = work_dir / "reports"

    for d in (pages_dir, preprocessed_dir, ocr_dir, gt_dir, metrics_dir, reports_dir):
        d.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Phase 1: Deterministic PDF Rendering (R2)
    # -------------------------------------------------------------------------
    rendered_manifest = render_pdf(
        pdf_path=synthetic_pdf,
        output_dir=pages_dir,
        dpi=300,
        pages="all",
        document_id="synthetic_archive_vol1",
    )
    assert rendered_manifest.rendered_pages_count == 2
    assert (pages_dir / "synthetic_archive_vol1_p0001.png").is_file()
    assert (pages_dir / "synthetic_archive_vol1_p0002.png").is_file()
    assert (pages_dir / "synthetic_archive_vol1_rendered_manifest.json").is_file()

    # -------------------------------------------------------------------------
    # Phase 2: Preprocessing Filter Pipeline (R4)
    # -------------------------------------------------------------------------
    pipeline = PreprocessingPipeline.from_spec("grayscale,clahe")
    p1_img = pages_dir / "synthetic_archive_vol1_p0001.png"
    p1_prep = preprocessed_dir / "synthetic_archive_vol1_p0001_grayscale,clahe.png"

    proc_img, proc_meta, proc_path = pipeline.process_file(p1_img, p1_prep)
    assert p1_prep.is_file()
    assert proc_path == p1_prep
    assert proc_meta["filter_names"] == ["grayscale", "clahe"]

    # -------------------------------------------------------------------------
    # Phase 3: Common OCR Execution (Mock Engine) (R3)
    # -------------------------------------------------------------------------
    adapter = MockOCRAdapter()
    assert adapter.is_available()

    # Define deterministic text for Page 1
    p1_text = "HISTORICAL PAPERS AND SPEECHES OF DR. BABASAHEB AMBEDKAR"
    ocr_res_p1 = adapter.process_image(
        image_path=p1_prep,
        language="eng",
        options={"text": p1_text, "filters": ["grayscale", "clahe"]},
    )
    ocr_res_p1_file = ocr_dir / "synthetic_archive_vol1_p0001_mock.json"
    ocr_res_p1.to_json_file(ocr_res_p1_file)
    assert ocr_res_p1_file.is_file()
    assert ocr_res_p1.status == "success"
    assert len(ocr_res_p1.regions) == 8

    # Process Page 2
    ocr_res_p2 = adapter.process_image(
        image_path=pages_dir / "synthetic_archive_vol1_p0002.png",
        language="eng",
        options={"text": "ANNIHILATION OF CASTE WITH A REPLY", "filters": ["raw"]},
    )
    ocr_res_p2_file = ocr_dir / "synthetic_archive_vol1_p0002_mock.json"
    ocr_res_p2.to_json_file(ocr_res_p2_file)
    assert ocr_res_p2_file.is_file()

    # -------------------------------------------------------------------------
    # Phase 4: Ground Truth & Evaluation (R5)
    # -------------------------------------------------------------------------
    # Curate Ground Truth ONLY for Page 1 (Page 2 exercises the unavailable protocol)
    gt_p1 = GroundTruthPage(
        document_id="synthetic_archive_vol1",
        page_id="synthetic_archive_vol1_p0001",
        reference_text="HISTORICAL PAPERS AND SPEECHES OF DR. BABASAHEB AMBEDKAR",
        language="eng",
        script="Latn",
        annotator="Synthetic Ground Truth Generator",
        verification_status="verified",
        regions=[
            GroundTruthRegion(region_id="r1", type="word", text="HISTORICAL", bbox=[50, 100, 120, 30]),
            GroundTruthRegion(region_id="r2", type="word", text="PAPERS", bbox=[180, 100, 90, 30]),
            GroundTruthRegion(region_id="r3", type="word", text="AND", bbox=[280, 100, 50, 30]),
            GroundTruthRegion(region_id="r4", type="word", text="SPEECHES", bbox=[340, 100, 110, 30]),
            GroundTruthRegion(region_id="r5", type="word", text="OF", bbox=[460, 100, 40, 30]),
            GroundTruthRegion(region_id="r6", type="word", text="DR.", bbox=[510, 100, 50, 30]),
            GroundTruthRegion(region_id="r7", type="word", text="BABASAHEB", bbox=[570, 100, 140, 30]),
            GroundTruthRegion(region_id="r8", type="word", text="AMBEDKAR", bbox=[720, 100, 130, 30]),
        ],
    )
    gt_p1.to_json_file(gt_dir / "synthetic_archive_vol1_p0001.json")

    eval_ret = evaluate_ocr.main([
        "--hypothesis", str(ocr_dir),
        "--ground-truth", str(gt_dir),
        "--output", str(metrics_dir),
        "--normalize",
        "--format", "both",
    ])
    assert eval_ret == 0

    # Verify evaluated metric files
    p1_metrics_file = metrics_dir / "synthetic_archive_vol1_p0001_mock_metrics.json"
    p2_metrics_file = metrics_dir / "synthetic_archive_vol1_p0002_mock_metrics.json"
    summary_file = metrics_dir / "summary_metrics.json"

    assert p1_metrics_file.is_file()
    assert p2_metrics_file.is_file()
    assert summary_file.is_file()

    summary = SummaryMetrics.from_json_file(summary_file)
    assert summary.total_pages == 2
    assert summary.evaluated_pages == 1
    assert summary.unavailable_pages == 1
    assert summary.mean_cer == 0.0
    assert summary.mean_wer == 0.0

    # -------------------------------------------------------------------------
    # Phase 5: Publication Report & Visualization (R6)
    # -------------------------------------------------------------------------
    rep_ret = generate_report.main([
        "--metrics", str(metrics_dir),
        "--output", str(reports_dir),
        "--format", "all",
        "--title", "E2E Synthetic Benchmark Test Report",
    ])
    assert rep_ret == 0

    assert (reports_dir / "benchmark_report.md").is_file()
    assert (reports_dir / "benchmark_report.json").is_file()
    assert (reports_dir / "benchmark_report.csv").is_file()
    assert (reports_dir / "cer_wer_comparison.png").is_file()
    assert (reports_dir / "error_breakdown.png").is_file()

    # Check Markdown report content integrity
    with open(reports_dir / "benchmark_report.md", "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "# E2E Synthetic Benchmark Test Report" in md_text
    assert "synthetic_archive_vol1_p0001" in md_text
    assert "synthetic_archive_vol1_p0002" in md_text
    assert "ground_truth_unavailable" in md_text
    assert "cer_wer_comparison.png" in md_text
    assert "error_breakdown.png" in md_text
