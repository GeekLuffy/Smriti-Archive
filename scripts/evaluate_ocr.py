#!/usr/bin/env python3
"""
CLI Tool: Standardized OCR Evaluation Engine (SIH26096 Requirement R5).

Evaluates OCR hypothesis JSON records against manually curated ground truth reference annotations.
Computes Character Error Rate (CER), Word Error Rate (WER) with exact (S, D, I) edit decompositions,
geometric bounding box IoU precision/recall/F1, and reading order alignment.

Enforces explicit 'ground_truth_unavailable' status when ground truth is missing.
"""

import argparse
from pathlib import Path
import sys
from typing import List, Optional

# Ensure src is in python path if run as standalone script
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sih_archive.evaluation.cer_wer import compute_cer, compute_wer
from sih_archive.evaluation.iou import match_bounding_boxes
from sih_archive.evaluation.reading_order import KendallTauReadingOrderEvaluator
from sih_archive.schemas.evaluation import (
    BoundingBoxMetrics,
    GroundTruthPage,
    PageMetrics,
    SummaryMetrics,
)
from sih_archive.schemas.ocr import OCROutput


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standardized OCR Error Metrics & Evaluation Engine (SIH26096 Requirement R5)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--hypothesis",
        "-i",
        required=True,
        type=str,
        help="Path to an OCR hypothesis JSON file or directory containing OCR JSON files.",
    )
    parser.add_argument(
        "--ground-truth",
        "-g",
        required=True,
        type=str,
        help="Path to a Ground Truth JSON file or directory containing ground truth JSON files.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="outputs/metrics",
        help="Directory to save evaluated page metrics and summary outputs.",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.5,
        help="Minimum IoU overlap threshold (tau) for bounding box bipartite matching.",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="both",
        choices=["json", "csv", "both"],
        help="Output serialization format for summary evaluation report ('json', 'csv', 'both').",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize whitespace and strip soft hyphens before computing CER and WER.",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Perform case-insensitive evaluation (converts strings to lowercase).",
    )
    return parser.parse_args(argv)


def get_hypothesis_files(hyp_path: Path) -> List[Path]:
    """Finds all candidate OCR output JSON files."""
    if hyp_path.is_file():
        return [hyp_path]
    if not hyp_path.is_dir():
        return []
    files = [
        p for p in sorted(hyp_path.iterdir())
        if p.is_file() and p.suffix.lower() == ".json"
        and not p.name.startswith(".")
        and not p.name.startswith("summary_")
        and not p.name.endswith("_metrics.json")
    ]
    return files


def find_ground_truth(page_id: str, document_id: str, gt_path: Path) -> Optional[Path]:
    """Resolves ground truth JSON path for a given page_id."""
    if gt_path.is_file():
        # Single ground truth file provided
        try:
            gt = GroundTruthPage.from_json_file(gt_path)
            if gt.page_id == page_id or page_id in gt_path.stem:
                return gt_path
        except Exception:
            return gt_path

    if gt_path.is_dir():
        candidates = [
            gt_path / f"{page_id}.json",
            gt_path / f"{page_id}_gt.json",
            gt_path / f"{document_id}_{page_id}.json",
        ]
        for c in candidates:
            if c.is_file():
                return c

        # Scan for partial match
        for f in gt_path.glob("*.json"):
            if f.stem == page_id or f.stem.startswith(page_id):
                return f

    return None


def evaluate_single_page(
    hyp_file: Path,
    gt_path: Path,
    iou_threshold: float,
    normalize: bool,
    ignore_case: bool,
) -> PageMetrics:
    """Evaluates an OCR hypothesis file against ground truth."""
    ocr_hyp = OCROutput.from_json_file(hyp_file)
    page_id = ocr_hyp.page_id
    doc_id = ocr_hyp.document_id
    engine = ocr_hyp.engine
    pipeline = ocr_hyp.processing.filters[0] if ocr_hyp.processing.filters else "raw"

    gt_file = find_ground_truth(page_id, doc_id, gt_path)

    if not gt_file or not gt_file.is_file():
        print(f"  [WARNING] Ground truth unavailable for page {page_id}. Skipping error metric calculation.")
        return PageMetrics.create_unavailable(
            document_id=doc_id,
            page_id=page_id,
            engine=engine,
            pipeline=pipeline,
            message=f"Ground truth unavailable: no reference annotation found in {gt_path} for {page_id}.",
        )

    gt_page = GroundTruthPage.from_json_file(gt_file)

    # Calculate CER & WER
    cer_breakdown = compute_cer(
        gt_page.reference_text,
        ocr_hyp.text,
        normalize=normalize,
        case_sensitive=not ignore_case,
    )
    wer_breakdown = compute_wer(
        gt_page.reference_text,
        ocr_hyp.text,
        normalize=normalize,
        case_sensitive=not ignore_case,
    )

    # Evaluate Bounding Boxes
    bbox_metrics: Optional[BoundingBoxMetrics] = None
    reading_order_score: Optional[float] = None

    if gt_page.regions:
        hyp_boxes = [r.bbox for r in ocr_hyp.regions]
        ref_boxes = [r.bbox for r in gt_page.regions]
        bbox_metrics, matched_pairs = match_bounding_boxes(
            hyp_boxes, ref_boxes, iou_threshold=iou_threshold
        )
        ro_evaluator = KendallTauReadingOrderEvaluator()
        ro_result = ro_evaluator.evaluate(
            matched_pairs,
            total_hyp_regions=len(hyp_boxes),
            total_ref_regions=len(ref_boxes),
        )
        reading_order_score = ro_result.get("score")

    return PageMetrics(
        document_id=doc_id,
        page_id=page_id,
        engine=engine,
        pipeline=pipeline,
        status="evaluated",
        message="Evaluation completed successfully.",
        cer=cer_breakdown.error_rate,
        wer=wer_breakdown.error_rate,
        cer_breakdown=cer_breakdown,
        wer_breakdown=wer_breakdown,
        bbox_metrics=bbox_metrics,
        reading_order_score=reading_order_score,
    )


def compute_summary(page_metrics: List[PageMetrics]) -> SummaryMetrics:
    """Aggregates page metrics into overall summary statistics."""
    evaluated = [p for p in page_metrics if p.status == "evaluated"]
    unavailable = [p for p in page_metrics if p.status == "ground_truth_unavailable"]
    errors = [p for p in page_metrics if p.status == "error"]

    mean_cer = sum(p.cer for p in evaluated if p.cer is not None) / len(evaluated) if evaluated else None
    mean_wer = sum(p.wer for p in evaluated if p.wer is not None) / len(evaluated) if evaluated else None

    # Geometric metrics
    with_bbox = [p for p in evaluated if p.bbox_metrics is not None]
    mean_prec = sum(p.bbox_metrics.precision for p in with_bbox) / len(with_bbox) if with_bbox else None
    mean_rec = sum(p.bbox_metrics.recall for p in with_bbox) / len(with_bbox) if with_bbox else None
    mean_f1 = sum(p.bbox_metrics.f1 for p in with_bbox) / len(with_bbox) if with_bbox else None
    mean_iou = sum(p.bbox_metrics.mean_iou for p in with_bbox) / len(with_bbox) if with_bbox else None

    # Reading order
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


def main(argv=None) -> int:
    args = parse_args(argv)
    hyp_path = Path(args.hypothesis)
    gt_path = Path(args.ground_truth)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not hyp_path.exists():
        print(f"ERROR: Hypothesis path not found: {hyp_path}", file=sys.stderr)
        return 1

    hyp_files = get_hypothesis_files(hyp_path)
    if not hyp_files:
        print(f"ERROR: No OCR hypothesis JSON files found at: {hyp_path}", file=sys.stderr)
        return 1

    print(f"=== SIH26096 OCR Standardized Evaluation Engine ===")
    print(f"Hypothesis:    {hyp_path} ({len(hyp_files)} file(s))")
    print(f"Ground Truth:  {gt_path}")
    print(f"Output Dir:    {out_dir}")
    print(f"IoU Threshold: {args.iou_threshold}")
    print(f"Normalize:     {args.normalize}")
    print(f"Ignore Case:   {args.ignore_case}")
    print(f"Format:        {args.format}\n")

    page_results: List[PageMetrics] = []

    for hyp_file in hyp_files:
        try:
            pm = evaluate_single_page(
                hyp_file,
                gt_path,
                iou_threshold=args.iou_threshold,
                normalize=args.normalize,
                ignore_case=args.ignore_case,
            )
            page_results.append(pm)

            # Save individual page metrics
            out_metric_file = out_dir / f"{hyp_file.stem}_metrics.json"
            pm.to_json_file(out_metric_file)

            if pm.status == "evaluated":
                cer_pct = (pm.cer * 100.0) if pm.cer is not None else 0.0
                wer_pct = (pm.wer * 100.0) if pm.wer is not None else 0.0
                f1_str = f"{pm.bbox_metrics.f1:.2f}" if pm.bbox_metrics else "N/A"
                print(f"  [EVAL] {pm.page_id} -> CER: {cer_pct:5.2f}% | WER: {wer_pct:5.2f}% | BBox F1: {f1_str}")
            else:
                print(f"  [{pm.status.upper()}] {pm.page_id} -> {pm.message}")

        except Exception as e:
            print(f"  [ERROR] {hyp_file.name} -> Evaluation failed: {e}", file=sys.stderr)
            err_pm = PageMetrics(
                document_id=hyp_file.stem.split("_p")[0] if "_p" in hyp_file.stem else hyp_file.stem,
                page_id=hyp_file.stem,
                status="error",
                message=f"Evaluation error: {e}",
            )
            page_results.append(err_pm)

    summary = compute_summary(page_results)

    # Save summary
    if args.format in ("json", "both"):
        summary_json_file = out_dir / "summary_metrics.json"
        summary.to_json_file(summary_json_file)
        print(f"\nSummary metrics written to: {summary_json_file}")

    if args.format in ("csv", "both"):
        summary_csv_file = out_dir / "summary_metrics.csv"
        summary.to_csv_file(summary_csv_file)
        print(f"Tabular summary CSV written to: {summary_csv_file}")

    # Print summary report
    print("\n================== EVALUATION SUMMARY ==================")
    print(f"Total Pages Processed:     {summary.total_pages}")
    print(f"Successfully Evaluated:    {summary.evaluated_pages}")
    print(f"Ground Truth Unavailable:  {summary.unavailable_pages}")
    print(f"Errors:                    {summary.error_pages}")
    if summary.evaluated_pages > 0:
        print(f"Mean CER:                  {summary.mean_cer * 100.0:.2f}% (CER: {summary.mean_cer:.4f})")
        print(f"Mean WER:                  {summary.mean_wer * 100.0:.2f}% (WER: {summary.mean_wer:.4f})")
        if summary.mean_f1 is not None:
            print(f"Mean BBox Precision:       {summary.mean_precision:.4f}")
            print(f"Mean BBox Recall:          {summary.mean_recall:.4f}")
            print(f"Mean BBox F1:              {summary.mean_f1:.4f}")
            print(f"Mean BBox IoU:             {summary.mean_iou:.4f}")
        if summary.mean_reading_order_score is not None:
            print(f"Mean Reading Order Score:  {summary.mean_reading_order_score:.4f}")
    print("========================================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
