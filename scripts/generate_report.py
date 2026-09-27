#!/usr/bin/env python3
"""
CLI Tool: Publication-Grade Benchmark Reporting & Visualizations (SIH26096 Requirement R6).

Aggregates OCR evaluation metrics (CER/WER edit distance breakdowns, bounding box IoU,
reading order consistency) across archival pages, documents, engines, and preprocessing
pipelines into publication-grade Markdown tables, structured JSON, tabular CSV,
and headless matplotlib visualization charts.
"""

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Enforce headless Agg backend for matplotlib before pyplot import
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sih_archive.schemas.evaluation import (
    BoundingBoxMetrics,
    EditOperationBreakdown,
    PageMetrics,
    SummaryMetrics,
)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publication-Grade OCR Benchmark Reporting & Visualization Engine (SIH26096 Requirement R6)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--metrics",
        "-m",
        required=True,
        type=str,
        help="Path to an evaluation metrics JSON file or directory containing metrics JSON files.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="outputs/reports",
        help="Destination directory for generated reports, tables, and visualization charts.",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        default="all",
        choices=["all", "markdown", "json", "csv", "chart"],
        help="Output serialization format ('all', 'markdown', 'json', 'csv', 'chart').",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="SIH26096 Archival OCR Benchmark Report (Phase E1)",
        help="Custom title header for publication report.",
    )
    return parser.parse_args(argv)


def load_metrics(metrics_path: Path) -> Tuple[SummaryMetrics, List[PageMetrics]]:
    """
    Loads PageMetrics and SummaryMetrics from a file or directory.
    Handles single PageMetrics, SummaryMetrics, or directory of metrics files.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics path does not exist: {metrics_path}")

    page_metrics_map: Dict[Tuple[str, Optional[str], Optional[str]], PageMetrics] = {}
    loaded_summary: Optional[SummaryMetrics] = None

    if metrics_path.is_file():
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if it's a SummaryMetrics file
        if "total_pages" in data and "page_metrics" in data:
            loaded_summary = SummaryMetrics.model_validate(data)
            for pm in loaded_summary.page_metrics:
                key = (pm.page_id, pm.engine, pm.pipeline)
                page_metrics_map[key] = pm
        elif isinstance(data, list):
            for item in data:
                pm = PageMetrics.model_validate(item)
                key = (pm.page_id, pm.engine, pm.pipeline)
                page_metrics_map[key] = pm
        else:
            # Single PageMetrics file
            pm = PageMetrics.model_validate(data)
            key = (pm.page_id, pm.engine, pm.pipeline)
            page_metrics_map[key] = pm

    elif metrics_path.is_dir():
        summary_file = metrics_path / "summary_metrics.json"
        if summary_file.is_file():
            try:
                loaded_summary = SummaryMetrics.from_json_file(summary_file)
                for pm in loaded_summary.page_metrics:
                    key = (pm.page_id, pm.engine, pm.pipeline)
                    page_metrics_map[key] = pm
            except Exception as e:
                print(f"[WARNING] Failed to load summary_metrics.json: {e}", file=sys.stderr)

        # Scan for all *_metrics.json
        for f in sorted(metrics_path.glob("*.json")):
            if f.name == "summary_metrics.json" or f.name.startswith("."):
                continue
            try:
                pm = PageMetrics.from_json_file(f)
                key = (pm.page_id, pm.engine, pm.pipeline)
                page_metrics_map[key] = pm
            except Exception:
                pass

    page_metrics = list(page_metrics_map.values())
    if not page_metrics and loaded_summary:
        page_metrics = loaded_summary.page_metrics

    # Compute fresh SummaryMetrics aggregating all collected pages
    summary = compute_summary(page_metrics)
    return summary, page_metrics


def compute_summary(page_metrics: List[PageMetrics]) -> SummaryMetrics:
    """Aggregates page metrics into overall summary statistics."""
    evaluated = [p for p in page_metrics if p.status == "evaluated"]
    unavailable = [p for p in page_metrics if p.status == "ground_truth_unavailable"]
    errors = [p for p in page_metrics if p.status == "error"]

    mean_cer = sum(p.cer for p in evaluated if p.cer is not None) / len(evaluated) if evaluated else None
    mean_wer = sum(p.wer for p in evaluated if p.wer is not None) / len(evaluated) if evaluated else None

    with_bbox = [p for p in evaluated if p.bbox_metrics is not None]
    mean_prec = sum(p.bbox_metrics.precision for p in with_bbox) / len(with_bbox) if with_bbox else None
    mean_rec = sum(p.bbox_metrics.recall for p in with_bbox) / len(with_bbox) if with_bbox else None
    mean_f1 = sum(p.bbox_metrics.f1 for p in with_bbox) / len(with_bbox) if with_bbox else None
    mean_iou = sum(p.bbox_metrics.mean_iou for p in with_bbox) / len(with_bbox) if with_bbox else None

    with_ro = [p for p in evaluated if p.reading_order_score is not None]
    mean_ro = sum(p.reading_order_score for p in with_ro) / len(with_ro) if with_ro else None

    return SummaryMetrics(
        total_pages=len(page_metrics),
        evaluated_pages=len(evaluated),
        unavailable_pages=len(unavailable),
        error_pages=len(errors),
        mean_cer=round(mean_cer, 4) if mean_cer is not None else None,
        mean_wer=round(mean_wer, 4) if mean_wer is not None else None,
        mean_precision=round(mean_prec, 4) if mean_prec is not None else None,
        mean_recall=round(mean_rec, 4) if mean_rec is not None else None,
        mean_f1=round(mean_f1, 4) if mean_f1 is not None else None,
        mean_iou=round(mean_iou, 4) if mean_iou is not None else None,
        mean_reading_order_score=round(mean_ro, 4) if mean_ro is not None else None,
        page_metrics=page_metrics,
    )


def generate_markdown_report(
    summary: SummaryMetrics,
    page_metrics: List[PageMetrics],
    title: str,
    output_dir: Path,
) -> str:
    """Generates clean, publication-grade markdown benchmark documentation."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    evaluated_pages = [p for p in page_metrics if p.status == "evaluated"]
    unavailable_pages = [p for p in page_metrics if p.status == "ground_truth_unavailable"]

    lines = [
        f"# {title}",
        "",
        f"**Generated**: {now_utc}  ",
        f"**Evaluation Scope**: Phase E1 Baseline Archival OCR & Preprocessing Benchmark  ",
        f"**Problem Statement**: SIH26096 (Digital Heritage Archive for Memorials, Manuscripts & Ambedkar)  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "| Metric | Value | Description |",
        "| :--- | :--- | :--- |",
        f"| **Total Processed Pages** | {summary.total_pages} | Total page records ingested across test runs |",
        f"| **Evaluated Pages** | {summary.evaluated_pages} | Pages with verified reference ground truth |",
        f"| **Ground Truth Unavailable** | {summary.unavailable_pages} | Pages skipped per research hygiene protocol |",
        f"| **Execution Errors** | {summary.error_pages} | Unhandled OCR or pipeline failures |",
    ]

    if summary.evaluated_pages > 0 and summary.mean_cer is not None:
        lines.extend([
            f"| **Mean Character Error Rate (CER)** | **{summary.mean_cer * 100.0:.2f}%** ({summary.mean_cer:.4f}) | Levenshtein edit distance over reference characters |",
            f"| **Mean Word Error Rate (WER)** | **{summary.mean_wer * 100.0:.2f}%** ({summary.mean_wer:.4f}) | Word-level Levenshtein edit distance |",
            f"| **Mean BBox Precision** | {summary.mean_precision:.4f} | Token bounding box overlap precision (IoU $\\ge$ 0.5) |",
            f"| **Mean BBox Recall** | {summary.mean_recall:.4f} | Token bounding box overlap recall (IoU $\\ge$ 0.5) |",
            f"| **Mean BBox F1-Score** | **{summary.mean_f1:.4f}** | Harmonic mean of bounding box precision and recall |",
            f"| **Mean BBox IoU** | {summary.mean_iou:.4f} | Mean Intersection over Union for true positive box matches |",
            f"| **Mean Reading Order Score** | {summary.mean_reading_order_score:.4f} | Kendall's Tau reading order consistency score $\\in [0, 1]$ |",
        ])
    else:
        lines.append("| **Evaluation Result** | *No ground truth pages available for quantitative CER/WER calculation* | Explicit null protocol maintained |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Preprocessing Pipeline Comparison",
        "",
        "Comparison of baseline performance across modular preprocessing pipelines:",
        "",
    ])

    # Group evaluated pages by pipeline
    pipeline_groups: Dict[str, List[PageMetrics]] = {}
    for p in evaluated_pages:
        pipe = p.pipeline or "raw"
        pipeline_groups.setdefault(pipe, []).append(p)

    if pipeline_groups:
        lines.extend([
            "| Preprocessing Pipeline | Pages | Mean CER (%) | Mean WER (%) | Mean BBox F1 | Mean IoU |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ])
        for pipe, group in sorted(pipeline_groups.items()):
            n = len(group)
            m_cer = sum(p.cer for p in group if p.cer is not None) / n if n else 0.0
            m_wer = sum(p.wer for p in group if p.wer is not None) / n if n else 0.0
            bbox_list = [p.bbox_metrics for p in group if p.bbox_metrics]
            m_f1 = sum(b.f1 for b in bbox_list) / len(bbox_list) if bbox_list else 0.0
            m_iou = sum(b.mean_iou for b in bbox_list) / len(bbox_list) if bbox_list else 0.0
            lines.append(f"| `{pipe}` | {n} | {m_cer * 100.0:6.2f}% | {m_wer * 100.0:6.2f}% | {m_f1:.4f} | {m_iou:.4f} |")
    else:
        lines.append("*No preprocessed variations with verified ground truth recorded.*")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Per-Page Evaluation Breakdown",
        "",
        "| Page ID | Engine | Pipeline | Status | CER (%) | WER (%) | BBox F1 | Mean IoU | Reading Order |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for pm in sorted(page_metrics, key=lambda x: (x.page_id, x.pipeline or "")):
        eng = pm.engine or "N/A"
        pipe = pm.pipeline or "raw"
        status_badge = f"`{pm.status}`"
        if pm.status == "evaluated":
            cer_str = f"{pm.cer * 100.0:5.2f}%" if pm.cer is not None else "N/A"
            wer_str = f"{pm.wer * 100.0:5.2f}%" if pm.wer is not None else "N/A"
            f1_str = f"{pm.bbox_metrics.f1:.4f}" if pm.bbox_metrics else "N/A"
            iou_str = f"{pm.bbox_metrics.mean_iou:.4f}" if pm.bbox_metrics else "N/A"
            ro_str = f"{pm.reading_order_score:.4f}" if pm.reading_order_score is not None else "N/A"
        else:
            cer_str = "null"
            wer_str = "null"
            f1_str = "null"
            iou_str = "null"
            ro_str = "null"
        lines.append(f"| `{pm.page_id}` | `{eng}` | `{pipe}` | {status_badge} | {cer_str} | {wer_str} | {f1_str} | {iou_str} | {ro_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Edit Operation Decompositions (CER & WER)",
        "",
        "Detailed Levenshtein edit operation breakdowns across verified pages ($S$: Substitutions, $D$: Deletions, $I$: Insertions):",
        "",
        "| Page ID | Pipeline | Ref Chars | Hyp Chars | Char S | Char D | Char I | Ref Words | Hyp Words | Word S | Word D | Word I |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    if evaluated_pages:
        for pm in sorted(evaluated_pages, key=lambda x: (x.page_id, x.pipeline or "")):
            pipe = pm.pipeline or "raw"
            cb = pm.cer_breakdown
            wb = pm.wer_breakdown
            c_ref = cb.reference_length if cb else 0
            c_hyp = cb.hypothesis_length if cb else 0
            c_s = cb.substitutions if cb else 0
            c_d = cb.deletions if cb else 0
            c_i = cb.insertions if cb else 0

            w_ref = wb.reference_length if wb else 0
            w_hyp = wb.hypothesis_length if wb else 0
            w_s = wb.substitutions if wb else 0
            w_d = wb.deletions if wb else 0
            w_i = wb.insertions if wb else 0

            lines.append(
                f"| `{pm.page_id}` | `{pipe}` | {c_ref} | {c_hyp} | {c_s} | {c_d} | {c_i} | {w_ref} | {w_hyp} | {w_s} | {w_d} | {w_i} |"
            )
    else:
        lines.append("| *None* | - | - | - | - | - | - | - | - | - | - | - |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Visual Benchmark Charts",
        "",
        "Visual diagnostic plots generated via headless Matplotlib rendering:",
        "",
        "### Character & Word Error Rate Comparison",
        "![CER vs WER Comparison](cer_wer_comparison.png)",
        "",
        "### Levenshtein Edit Operation Error Breakdown",
        "![Error Breakdown](error_breakdown.png)",
        "",
        "---",
        "",
        "## 6. Research Integrity & Methodology Notes",
        "",
        "1. **Zero-Fabrication Guarantee**: In adherence to SIH26096 Requirement R5 and research integrity principles, pages lacking verified ground truth are never assigned synthetic 0.0% error rates or simulated transcripts. They remain explicitly classified as `ground_truth_unavailable`.",
        "2. **Edit Distance Alignment**: Character Error Rate and Word Error Rate are computed using RapidFuzz Levenshtein edit operations decomposed into exact substitutions ($S$), deletions ($D$), and insertions ($I$). Normalization strips soft-hyphens (`\\u00ad`) and collapses whitespace without altering semantic tokens.",
        "3. **Geometric Region Matching**: Token bounding box matching uses greedy bipartite assignment at $\\tau = 0.5$ IoU threshold. Unmatched hypothesis boxes are penalized as false positives; omitted reference regions are counted as false negatives.",
        "4. **Downstream Phase Integration**: OCR token regions with bounding boxes and line/block indices are preserved in `outputs/ocr/*.json` to serve as the ground truth foundation for Phase E2 (lexical/dense retrieval) and Phase E3 (visual citation grounding).",
        "",
    ])

    return "\n".join(lines)


def generate_visualizations(
    summary: SummaryMetrics,
    page_metrics: List[PageMetrics],
    output_dir: Path,
) -> List[Path]:
    """
    Renders headless publication-grade Matplotlib charts.
    Returns paths to generated image files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_charts: List[Path] = []

    evaluated = [p for p in page_metrics if p.status == "evaluated" and p.cer is not None]

    # --- Chart 1: CER & WER Comparison ---
    cer_wer_path = output_dir / "cer_wer_comparison.png"
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)

    if evaluated:
        labels = [f"{p.page_id}\n({p.pipeline or 'raw'})" for p in evaluated]
        cer_vals = [p.cer * 100.0 for p in evaluated]
        wer_vals = [p.wer * 100.0 if p.wer is not None else 0.0 for p in evaluated]

        x = np.arange(len(labels))
        width = 0.35

        rects1 = ax.bar(x - width / 2, cer_vals, width, label="CER (%)", color="#1f77b4", edgecolor="#0e4369")
        rects2 = ax.bar(x + width / 2, wer_vals, width, label="WER (%)", color="#ff7f0e", edgecolor="#994600")

        ax.set_ylabel("Error Rate (%)", fontsize=11, fontweight="bold")
        ax.set_title("OCR Accuracy Benchmark: CER vs WER by Page & Pipeline", fontsize=13, fontweight="bold", pad=12)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        # Attach text labels above bars
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(
                    f"{height:.1f}%",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        autolabel(rects1)
        autolabel(rects2)
    else:
        ax.text(
            0.5,
            0.5,
            "No Evaluated Pages Available\n(All pages classified as ground_truth_unavailable)",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=12,
            color="#666666",
        )
        ax.set_title("OCR Accuracy Benchmark: CER vs WER (No Data)", fontsize=13, fontweight="bold")

    plt.tight_layout()
    fig.savefig(cer_wer_path, dpi=200)
    plt.close(fig)
    generated_charts.append(cer_wer_path)

    # --- Chart 2: Edit Operation Breakdown ---
    breakdown_path = output_dir / "error_breakdown.png"
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)

    if evaluated and any(p.cer_breakdown for p in evaluated):
        labels = [f"{p.page_id}\n({p.pipeline or 'raw'})" for p in evaluated]
        subs = [(p.cer_breakdown.substitutions if p.cer_breakdown else 0) for p in evaluated]
        dels = [(p.cer_breakdown.deletions if p.cer_breakdown else 0) for p in evaluated]
        ins = [(p.cer_breakdown.insertions if p.cer_breakdown else 0) for p in evaluated]

        x = np.arange(len(labels))
        width = 0.55

        p1 = ax.bar(x, subs, width, label="Substitutions (S)", color="#2ca02c", edgecolor="#155315")
        p2 = ax.bar(x, dels, width, bottom=subs, label="Deletions (D)", color="#d62728", edgecolor="#771314")
        p3 = ax.bar(x, ins, width, bottom=np.array(subs) + np.array(dels), label="Insertions (I)", color="#9467bd", edgecolor="#4e3366")

        ax.set_ylabel("Character Edit Count", fontsize=11, fontweight="bold")
        ax.set_title("Levenshtein Edit Operations Decomposition (S + D + I)", fontsize=13, fontweight="bold", pad=12)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        for i, total in enumerate(np.array(subs) + np.array(dels) + np.array(ins)):
            ax.annotate(
                f"Total: {total}",
                xy=(x[i], total),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )
    else:
        ax.text(
            0.5,
            0.5,
            "No Edit Breakdown Data Available\n(All pages classified as ground_truth_unavailable)",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=12,
            color="#666666",
        )
        ax.set_title("Edit Operations Decomposition (No Data)", fontsize=13, fontweight="bold")

    plt.tight_layout()
    fig.savefig(breakdown_path, dpi=200)
    plt.close(fig)
    generated_charts.append(breakdown_path)

    return generated_charts


def save_reports(
    summary: SummaryMetrics,
    page_metrics: List[PageMetrics],
    output_dir: Path,
    title: str,
    format_choice: str,
) -> Dict[str, Path]:
    """Generates and writes requested report formats to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Path] = {}

    # 1. Markdown Report
    if format_choice in ("all", "markdown"):
        md_text = generate_markdown_report(summary, page_metrics, title, output_dir)
        md_file = output_dir / "benchmark_report.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_text)
        results["markdown"] = md_file

    # 2. JSON Report
    if format_choice in ("all", "json"):
        json_file = output_dir / "benchmark_report.json"
        summary.to_json_file(json_file)
        results["json"] = json_file

    # 3. CSV Report
    if format_choice in ("all", "csv"):
        csv_file = output_dir / "benchmark_report.csv"
        summary.to_csv_file(csv_file)
        results["csv"] = csv_file

    # 4. Charts
    if format_choice in ("all", "chart"):
        chart_files = generate_visualizations(summary, page_metrics, output_dir)
        results["chart_cer_wer"] = chart_files[0]
        results["chart_breakdown"] = chart_files[1]

    return results


def main(argv=None) -> int:
    args = parse_args(argv)
    metrics_path = Path(args.metrics)
    output_dir = Path(args.output)

    try:
        summary, page_metrics = load_metrics(metrics_path)
    except Exception as e:
        print(f"ERROR: Failed to load evaluation metrics from '{metrics_path}': {e}", file=sys.stderr)
        return 1

    print(f"=== SIH26096 OCR Benchmark Report Generator ===")
    print(f"Metrics Source:    {metrics_path}")
    print(f"Total Pages:       {summary.total_pages}")
    print(f"Evaluated Pages:   {summary.evaluated_pages}")
    print(f"Unavailable Pages: {summary.unavailable_pages}")
    print(f"Errors:            {summary.error_pages}")
    print(f"Output Directory:  {output_dir}")
    print(f"Format:            {args.format}\n")

    try:
        generated = save_reports(
            summary=summary,
            page_metrics=page_metrics,
            output_dir=output_dir,
            title=args.title,
            format_choice=args.format,
        )

        for fmt, path in generated.items():
            print(f"  [CREATED] {fmt.upper()}: {path}")

        print("\nReport generation completed successfully.")
        return 0

    except Exception as e:
        print(f"ERROR: Failed to generate benchmark reports: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
