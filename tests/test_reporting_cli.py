"""
Unit and CLI Integration Tests for scripts/generate_report.py (SIH26096 Requirement R6).
"""

import json
from pathlib import Path
import subprocess
import sys
import pytest

# Ensure scripts and src are accessible
repo_root = Path(__file__).resolve().parent.parent
scripts_dir = repo_root / "scripts"
src_dir = repo_root / "src"
for d in (scripts_dir, src_dir):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from generate_report import (
    compute_summary,
    generate_markdown_report,
    generate_visualizations,
    load_metrics,
    main,
    save_reports,
)
from sih_archive.schemas.evaluation import (
    BoundingBoxMetrics,
    EditOperationBreakdown,
    PageMetrics,
    SummaryMetrics,
)


@pytest.fixture
def sample_metrics_dir(tmp_path):
    """Creates a temporary directory with synthetic page metrics and summary."""
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()

    pm1 = PageMetrics(
        document_id="synth_doc",
        page_id="synth_doc_p0001",
        engine="mock",
        pipeline="raw",
        status="evaluated",
        cer=0.04,
        wer=0.08,
        cer_breakdown=EditOperationBreakdown(
            substitutions=1, deletions=0, insertions=1,
            reference_length=50, hypothesis_length=51,
            total_distance=2, error_rate=0.04,
        ),
        wer_breakdown=EditOperationBreakdown(
            substitutions=1, deletions=0, insertions=0,
            reference_length=12, hypothesis_length=12,
            total_distance=1, error_rate=0.0833,
        ),
        bbox_metrics=BoundingBoxMetrics(
            total_hypothesis_boxes=12, total_reference_boxes=12,
            true_positives=11, false_positives=1, false_negatives=1,
            precision=0.9167, recall=0.9167, f1=0.9167, mean_iou=0.88,
            iou_threshold=0.5, matched_pairs_count=11,
        ),
        reading_order_score=1.0,
    )
    pm1.to_json_file(metrics_dir / "synth_doc_p0001_metrics.json")

    pm2 = PageMetrics.create_unavailable("synth_doc", "synth_doc_p0002", engine="mock", pipeline="raw")
    pm2.to_json_file(metrics_dir / "synth_doc_p0002_metrics.json")

    summary = SummaryMetrics(
        total_pages=2,
        evaluated_pages=1,
        unavailable_pages=1,
        error_pages=0,
        mean_cer=0.04,
        mean_wer=0.0833,
        mean_precision=0.9167,
        mean_recall=0.9167,
        mean_f1=0.9167,
        mean_iou=0.88,
        mean_reading_order_score=1.0,
        page_metrics=[pm1, pm2],
    )
    summary.to_json_file(metrics_dir / "summary_metrics.json")

    return metrics_dir


def test_cli_generate_report_help():
    """Verify that python scripts/generate_report.py --help returns exit code 0."""
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "generate_report.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Publication-Grade OCR Benchmark Reporting" in result.stdout
    assert "--metrics" in result.stdout
    assert "--format" in result.stdout


def test_load_metrics_from_directory(sample_metrics_dir):
    summary, page_metrics = load_metrics(sample_metrics_dir)
    assert summary.total_pages == 2
    assert summary.evaluated_pages == 1
    assert summary.unavailable_pages == 1
    assert len(page_metrics) == 2


def test_load_metrics_from_single_summary_file(sample_metrics_dir):
    summary_file = sample_metrics_dir / "summary_metrics.json"
    summary, page_metrics = load_metrics(summary_file)
    assert summary.total_pages == 2
    assert len(page_metrics) == 2


def test_load_metrics_from_single_page_file(sample_metrics_dir):
    page_file = sample_metrics_dir / "synth_doc_p0001_metrics.json"
    summary, page_metrics = load_metrics(page_file)
    assert summary.total_pages == 1
    assert summary.evaluated_pages == 1
    assert len(page_metrics) == 1
    assert page_metrics[0].page_id == "synth_doc_p0001"


def test_generate_markdown_report_formatting(sample_metrics_dir, tmp_path):
    summary, page_metrics = load_metrics(sample_metrics_dir)
    md_content = generate_markdown_report(summary, page_metrics, "Custom Title", tmp_path)
    assert "# Custom Title" in md_content
    assert "Executive Summary" in md_content
    assert "synth_doc_p0001" in md_content
    assert "synth_doc_p0002" in md_content
    assert "ground_truth_unavailable" in md_content
    assert "cer_wer_comparison.png" in md_content


def test_generate_visualizations(sample_metrics_dir, tmp_path):
    summary, page_metrics = load_metrics(sample_metrics_dir)
    out_dir = tmp_path / "charts"
    charts = generate_visualizations(summary, page_metrics, out_dir)
    assert len(charts) == 2
    assert (out_dir / "cer_wer_comparison.png").is_file()
    assert (out_dir / "error_breakdown.png").is_file()
    assert (out_dir / "cer_wer_comparison.png").stat().st_size > 1000
    assert (out_dir / "error_breakdown.png").stat().st_size > 1000


def test_save_reports_all_formats(sample_metrics_dir, tmp_path):
    summary, page_metrics = load_metrics(sample_metrics_dir)
    out_dir = tmp_path / "reports_all"
    generated = save_reports(
        summary=summary,
        page_metrics=page_metrics,
        output_dir=out_dir,
        title="Benchmark Test",
        format_choice="all",
    )
    assert "markdown" in generated
    assert "json" in generated
    assert "csv" in generated
    assert "chart_cer_wer" in generated
    assert "chart_breakdown" in generated
    for path in generated.values():
        assert path.is_file()


def test_cli_execution_all_formats(sample_metrics_dir, tmp_path):
    out_dir = tmp_path / "cli_reports"
    ret = main([
        "--metrics", str(sample_metrics_dir),
        "--output", str(out_dir),
        "--format", "all",
    ])
    assert ret == 0
    assert (out_dir / "benchmark_report.md").is_file()
    assert (out_dir / "benchmark_report.json").is_file()
    assert (out_dir / "benchmark_report.csv").is_file()
    assert (out_dir / "cer_wer_comparison.png").is_file()
    assert (out_dir / "error_breakdown.png").is_file()


def test_cli_execution_only_markdown(sample_metrics_dir, tmp_path):
    out_dir = tmp_path / "cli_md_only"
    ret = main([
        "--metrics", str(sample_metrics_dir),
        "--output", str(out_dir),
        "--format", "markdown",
    ])
    assert ret == 0
    assert (out_dir / "benchmark_report.md").is_file()
    assert not (out_dir / "benchmark_report.json").exists()
    assert not (out_dir / "cer_wer_comparison.png").exists()


def test_cli_execution_missing_metrics_path(tmp_path):
    ret = main([
        "--metrics", str(tmp_path / "nonexistent_dir"),
        "--output", str(tmp_path / "out"),
    ])
    assert ret == 1


def test_empty_evaluated_pages_handling(tmp_path):
    """Ensure report and charts handle 0 evaluated pages (all unavailable) gracefully."""
    pm_unavail = PageMetrics.create_unavailable("doc1", "doc1_p0001", "mock", "raw")
    summary = compute_summary([pm_unavail])
    out_dir = tmp_path / "empty_eval"

    generated = save_reports(summary, [pm_unavail], out_dir, "Empty Evaluation", "all")
    assert (out_dir / "benchmark_report.md").is_file()
    assert (out_dir / "cer_wer_comparison.png").is_file()
    assert (out_dir / "error_breakdown.png").is_file()
