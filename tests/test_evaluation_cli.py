"""Unit and integration tests for scripts/evaluate_ocr.py CLI (Requirement R5/R7)."""

import json
from pathlib import Path
import pytest

from scripts.evaluate_ocr import main as cli_evaluate_main
from sih_archive.schemas.evaluation import GroundTruthPage, GroundTruthRegion, PageMetrics, SummaryMetrics
from sih_archive.schemas.ocr import OCROutput, ProcessingMetadata, TokenRegion


@pytest.fixture
def synthetic_ocr_output(tmp_path: Path) -> Path:
    """Creates a synthetic OCR hypothesis JSON file."""
    ocr_file = tmp_path / "hypotheses" / "sample_doc_p0001_mock_raw.json"
    data = OCROutput(
        document_id="sample_doc",
        page_id="sample_doc_p0001",
        language="eng",
        script="Latn",
        engine="mock",
        engine_version="1.0",
        image_path="data/processed/pages/sample_doc_p0001.png",
        processing=ProcessingMetadata(dpi=300, filters=["raw"], duration_ms=10.0),
        text="Dr. Babasaheb Ambedkar Writings",
        regions=[
            TokenRegion(type="word", text="Dr.", bbox=[10, 10, 40, 20], confidence=95.0),
            TokenRegion(type="word", text="Babasaheb", bbox=[55, 10, 80, 20], confidence=94.0),
            TokenRegion(type="word", text="Ambedkar", bbox=[140, 10, 80, 20], confidence=96.0),
            TokenRegion(type="word", text="Writings", bbox=[10, 40, 70, 20], confidence=92.0),
        ],
        status="success",
    )
    data.to_json_file(ocr_file)
    return ocr_file


@pytest.fixture
def synthetic_ground_truth(tmp_path: Path) -> Path:
    """Creates a matching synthetic Ground Truth JSON file."""
    gt_file = tmp_path / "ground_truth" / "sample_doc_p0001.json"
    gt = GroundTruthPage(
        document_id="sample_doc",
        page_id="sample_doc_p0001",
        reference_text="Dr. Babasaheb Ambedkar Writings\n",
        language="eng",
        script="Latn",
        annotator="Test Annotator",
        annotation_date="2026-09-27",
        verification_status="verified",
        regions=[
            GroundTruthRegion(region_id="w1", type="word", text="Dr.", bbox=[10, 10, 40, 20], reading_order_index=0),
            GroundTruthRegion(region_id="w2", type="word", text="Babasaheb", bbox=[55, 10, 80, 20], reading_order_index=1),
            GroundTruthRegion(region_id="w3", type="word", text="Ambedkar", bbox=[140, 10, 80, 20], reading_order_index=2),
            GroundTruthRegion(region_id="w4", type="word", text="Writings", bbox=[10, 40, 70, 20], reading_order_index=3),
        ],
    )
    gt.to_json_file(gt_file)
    return gt_file


def test_cli_evaluate_ocr_help():
    """Verify scripts/evaluate_ocr.py --help executes cleanly with code 0."""
    with pytest.raises(SystemExit) as exc:
        cli_evaluate_main(["--help"])
    assert exc.value.code == 0


def test_cli_evaluate_single_page_success(synthetic_ocr_output: Path, synthetic_ground_truth: Path, tmp_path: Path):
    """Verify single-page evaluation against ground truth."""
    out_dir = tmp_path / "metrics_out"
    exit_code = cli_evaluate_main([
        "-i", str(synthetic_ocr_output),
        "-g", str(synthetic_ground_truth),
        "-o", str(out_dir),
        "--normalize",
        "--format", "both",
    ])
    assert exit_code == 0

    metric_file = out_dir / f"{synthetic_ocr_output.stem}_metrics.json"
    assert metric_file.is_file()

    pm = PageMetrics.from_json_file(metric_file)
    assert pm.status == "evaluated"
    assert pm.cer == 0.0
    assert pm.wer == 0.0
    assert pm.bbox_metrics is not None
    assert pm.bbox_metrics.precision == 1.0
    assert pm.bbox_metrics.recall == 1.0
    assert pm.bbox_metrics.f1 == 1.0
    assert pm.reading_order_score == 1.0

    # Verify summary JSON and CSV
    summary_json = out_dir / "summary_metrics.json"
    summary_csv = out_dir / "summary_metrics.csv"
    assert summary_json.is_file()
    assert summary_csv.is_file()

    summary = SummaryMetrics.from_json_file(summary_json)
    assert summary.total_pages == 1
    assert summary.evaluated_pages == 1
    assert summary.mean_cer == 0.0


def test_cli_evaluate_ground_truth_unavailable(synthetic_ocr_output: Path, tmp_path: Path):
    """
    Verify explicit ground_truth_unavailable protocol:
    when ground truth is missing, records explicit null metrics without crashing.
    """
    out_dir = tmp_path / "metrics_out"
    empty_gt_dir = tmp_path / "empty_gt"
    empty_gt_dir.mkdir(parents=True, exist_ok=True)

    exit_code = cli_evaluate_main([
        "-i", str(synthetic_ocr_output),
        "-g", str(empty_gt_dir),
        "-o", str(out_dir),
    ])
    assert exit_code == 0

    metric_file = out_dir / f"{synthetic_ocr_output.stem}_metrics.json"
    assert metric_file.is_file()

    pm = PageMetrics.from_json_file(metric_file)
    assert pm.status == "ground_truth_unavailable"
    assert pm.cer is None
    assert pm.wer is None
    assert pm.cer_breakdown is None
    assert pm.wer_breakdown is None
    assert pm.bbox_metrics is None
    assert pm.reading_order_score is None

    summary_json = out_dir / "summary_metrics.json"
    summary = SummaryMetrics.from_json_file(summary_json)
    assert summary.evaluated_pages == 0
    assert summary.unavailable_pages == 1
    assert summary.mean_cer is None


def test_cli_evaluate_batch_directory(synthetic_ocr_output: Path, synthetic_ground_truth: Path, tmp_path: Path):
    """Verify batch evaluation over directory containing multiple OCR outputs."""
    hyp_dir = synthetic_ocr_output.parent
    gt_dir = synthetic_ground_truth.parent
    out_dir = tmp_path / "batch_metrics"

    # Add a second page without ground truth
    ocr_file_2 = hyp_dir / "sample_doc_p0002_mock_raw.json"
    ocr_2 = OCROutput(
        document_id="sample_doc",
        page_id="sample_doc_p0002",
        language="eng",
        engine="mock",
        image_path="sample.png",
        processing=ProcessingMetadata(dpi=300),
        text="Unannotated Page",
        regions=[],
    )
    ocr_2.to_json_file(ocr_file_2)

    exit_code = cli_evaluate_main([
        "-i", str(hyp_dir),
        "-g", str(gt_dir),
        "-o", str(out_dir),
        "--format", "both",
    ])
    assert exit_code == 0

    summary = SummaryMetrics.from_json_file(out_dir / "summary_metrics.json")
    assert summary.total_pages == 2
    assert summary.evaluated_pages == 1
    assert summary.unavailable_pages == 1


def test_cli_evaluate_missing_inputs(tmp_path: Path):
    """Verify CLI returns exit code 1 when input directory does not exist or has no JSONs."""
    assert cli_evaluate_main(["-i", str(tmp_path / "nonexistent"), "-g", str(tmp_path)]) == 1
