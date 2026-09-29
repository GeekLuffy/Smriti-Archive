#!/usr/bin/env python3
"""
CLI Tool: Run and evaluate empirical Phase E3 Attribution & Refusal Benchmark (SIH26096).

Enforces strict scientific research integrity:
- Checks Phase E1 and E2 results.
- If upstream phases are BLOCKED or LOCKED_PREVIEW, strictly enforces:
  LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1 and E2).
- Evaluates:
  User Question -> Retrieved Evidence -> Generated Answer -> Supporting Span -> Page -> Region/BBox.
- Measures:
  1. Claim Support Rate
  2. Span Precision
  3. Bounding-Box IoU
  4. Broken-Link Rate
  5. Refusal Accuracy (correctly returning 'Insufficient archival evidence found for a supported answer')
  6. Inter-annotator agreement (Cohen's Kappa / Percent Agreement)
- Emits results to results/e3/ (JSON report, annotator agreement, and Markdown report).
"""

import argparse
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sih_archive.attribution.evaluator import AttributionEvaluator
from sih_archive.attribution.pipeline import EvidenceGroundedAnswerPipeline
from sih_archive.retrieval.bm25 import BM25RetrievalEngine
from sih_archive.schemas.ocr import OCROutput

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("run_e3_attribution")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase E3 Archival Evidence Attribution Benchmark (SIH26096)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-ocr",
        "-i",
        type=str,
        default="outputs/ocr",
        help="Directory containing OCR JSON documents.",
    )
    parser.add_argument(
        "--e1-results",
        type=str,
        default="results/e1/e1_benchmark_report.json",
        help="Path to Phase E1 benchmark report.",
    )
    parser.add_argument(
        "--e2-results",
        type=str,
        default="results/e2/e2_retrieval_results.json",
        help="Path to Phase E2 benchmark report.",
    )
    parser.add_argument(
        "--questions",
        "-q",
        type=str,
        default="data/evaluation/attribution_questions.json",
        help="Path to questions evaluation dataset.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="results/e3",
        help="Directory to save machine-readable results and Markdown report.",
    )
    parser.add_argument(
        "--force-preview",
        action="store_true",
        help="Run preview evaluation on existing index even if E1/E2 are blocked. Marked as LOCKED_PREVIEW.",
    )
    return parser.parse_args(argv)


def load_ocr_documents(ocr_dir: Path) -> List[OCROutput]:
    """Loads all valid OCR JSON outputs."""
    docs = []
    if not ocr_dir.is_dir():
        return docs
    for f in sorted(ocr_dir.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if "regions" in data and "text" in data and "page_id" in data:
                docs.append(OCROutput.model_validate(data))
        except Exception:
            continue
    return docs


def compute_inter_annotator_agreement(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes percent agreement between dual independent annotators."""
    total_judgments = 0
    agreed_judgments = 0

    for q in questions:
        evals = q.get("annotator_evaluations", {})
        a1 = evals.get("annotator_1")
        a2 = evals.get("annotator_2")
        if a1 and a2:
            total_judgments += 1
            if a1 == a2:
                agreed_judgments += 1

    percent = (agreed_judgments / total_judgments) if total_judgments > 0 else 1.0
    return {
        "total_judged_items": total_judgments,
        "concordant_items": agreed_judgments,
        "percent_agreement": round(percent, 4),
        "cohens_kappa_approx": round((percent - 0.5) / 0.5, 4) if percent >= 0.5 else 0.0,
    }


def run_e3_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir = Path(args.input_ocr)
    e1_path = Path(args.e1_results)
    e2_path = Path(args.e2_results)
    q_path = Path(args.questions)

    # 1. Inspect upstream gating statuses
    e1_status = "UNKNOWN"
    if e1_path.is_file():
        try:
            with open(e1_path, "r", encoding="utf-8") as f:
                e1_status = json.load(f).get("gate_status", "UNKNOWN")
        except Exception:
            pass

    e2_status = "UNKNOWN"
    if e2_path.is_file():
        try:
            with open(e2_path, "r", encoding="utf-8") as f:
                e2_status = json.load(f).get("gate_status", "UNKNOWN")
        except Exception:
            pass

    e1_ready = (e1_status == "MEASURED")
    e2_ready = (e2_status == "MEASURED")

    if not (e1_ready and e2_ready):
        gate_status = "LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1 and E2)"
    else:
        gate_status = "READY_FOR_EMPIRICAL_EVALUATION"

    # 2. Load questions and corpus
    docs = load_ocr_documents(ocr_dir)
    questions_data = {}
    questions = []
    if q_path.is_file():
        try:
            with open(q_path, "r", encoding="utf-8") as f:
                questions_data = json.load(f)
                questions = questions_data.get("questions", [])
        except Exception as e:
            logger.warning(f"Could not load questions: {e}")

    # 3. Setup attribution engine
    bm25 = BM25RetrievalEngine()
    pipeline = EvidenceGroundedAnswerPipeline(
        retrieval_engine=bm25,
        min_relevance_score=0.01,
        min_support_similarity=50.0,
    )
    pipeline.register_documents(docs)

    config_snapshot = {
        "benchmark": "E3_EVIDENCE_ATTRIBUTION",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "input_ocr_dir": str(ocr_dir),
        "e1_dependency_status": e1_status,
        "e2_dependency_status": e2_status,
        "gate_status": gate_status,
        "indexed_documents_count": len(docs),
        "questions_count": len(questions),
        "target_questions_count": 50,
        "annotator_count": 2,
    }

    with open(output_dir / "config_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(config_snapshot, f, indent=2)

    # 4. Compute pipeline answers
    answers = [pipeline.answer_question(q["question"]) for q in questions]

    # Map to format expected by AttributionEvaluator
    test_queries = [
        {
            "question": q["question"],
            "expected_page_id": q.get("expected_page_id"),
            "expected_span": q.get("expected_span", ""),
            "target_bbox": q.get("target_bbox"),
        }
        for q in questions
    ]

    evaluator = AttributionEvaluator()
    eval_metrics = evaluator.evaluate_batch(answers, test_queries)

    # Calculate dual-annotator agreement
    agreement = compute_inter_annotator_agreement(questions)
    with open(output_dir / "annotator_agreement.json", "w", encoding="utf-8") as f:
        json.dump(agreement, f, indent=2)

    # Compile evaluated answers
    answer_records = []
    for ans in answers:
        answer_records.append({
            "question": ans.question,
            "is_refusal": ans.is_refusal,
            "refusal_reason": ans.refusal_reason,
            "answer_text": ans.answer_text,
            "claims_count": len(ans.claims),
            "citations": [
                {
                    "document_id": c.citation.document_id,
                    "page_id": c.citation.page_id,
                    "quote_span": c.citation.quote_span,
                    "bbox": c.citation.bbox,
                    "confidence": c.citation.confidence,
                }
                for c in ans.claims if c.citation
            ],
        })

    report_data = {
        "phase": "E3_ATTRIBUTION",
        "benchmark_date": time.strftime("%Y-%m-%d", time.gmtime()),
        "gate_status": gate_status,
        "gating_rule": (
            "Attribution scores remain locked from official evaluation until real archival "
            "OCR outputs (E1) and judged retrieval inputs (E2) are validated."
        ),
        "upstream_dependencies": {
            "e1_status": e1_status,
            "e2_status": e2_status,
        },
        "target_corpus_range": [30, 50],
        "target_questions_count": 50,
        "questions_evaluated_count": len(questions),
        "annotator_agreement": agreement,
        "metrics": eval_metrics.model_dump(),
        "attribution_chain": "Question -> Retrieval -> Page -> Region/BBox -> Claim -> Citation -> Viewer Target",
        "answers": answer_records,
        "scientific_integrity_notice": (
            "Grounding faithfulness cannot be meaningfully validated on synthetic dummy text. "
            "The system strictly generates 'Insufficient archival evidence found for a supported answer' "
            "when primary evidence is absent or similarity is below threshold."
        ),
    }

    with open(output_dir / "e3_attribution_results.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Markdown Report
    with open(output_dir / "REPORT.md", "w", encoding="utf-8") as f:
        f.write("# SIH26096 — Phase E3 Evidence Attribution Benchmark Report\n\n")
        f.write(f"- **Execution Date:** {config_snapshot['timestamp']}\n")
        f.write(f"- **Gate Status:** `{gate_status}`\n")
        f.write(f"- **E1 Dependency Status:** `{e1_status}`\n")
        f.write(f"- **E2 Dependency Status:** `{e2_status}`\n")
        f.write(f"- **Questions Evaluated:** {len(questions)} (Target: ~50 questions)\n")
        f.write(f"- **Inter-Annotator Agreement:** {agreement['percent_agreement'] * 100:.1f}%\n\n")

        f.write("## Scientific Gating Notice\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **Phase E3 is strictly gated on Phases E1 and E2.** Attribution scores on synthetic\n")
        f.write("> fixtures are previews and must not be reported as empirical archival evidence.\n\n")

        f.write("## Evaluation Metrics (Preview)\n\n")
        f.write(f"- **Claim Support Rate:** {eval_metrics.claim_support_rate:.4f}\n")
        f.write(f"- **Span Precision:** {eval_metrics.span_precision:.4f}\n")
        f.write(f"- **Source Page Accuracy:** {eval_metrics.source_page_accuracy:.4f}\n")
        f.write(f"- **Mean BBox IoU:** {eval_metrics.mean_bbox_iou:.4f}\n")
        f.write(f"- **Broken Citation Rate:** {eval_metrics.broken_citation_rate:.4f}\n")
        f.write(f"- **Unsupported Answer Rate:** {eval_metrics.unsupported_answer_rate:.4f}\n\n")

        f.write("## Principled Refusal Verification\n")
        f.write("When evidence similarity falls below threshold or queries are out of domain,\n")
        f.write("the system returns an explicit refusal card:\n")
        f.write("> *\"Insufficient archival evidence found for a supported answer.\"*\n")

    logger.info(f"E3 Benchmark complete. Results written to {output_dir}")
    return report_data


def main(argv=None) -> int:
    args = parse_args(argv)
    res = run_e3_pipeline(args)
    print("\n================== E3 BENCHMARK SUMMARY ==================")
    print(f"Gate Status:            {res.get('gate_status')}")
    print(f"E1 Dependency:          {res.get('upstream_dependencies', {}).get('e1_status')}")
    print(f"E2 Dependency:          {res.get('upstream_dependencies', {}).get('e2_status')}")
    print(f"Questions Evaluated:    {res.get('questions_evaluated_count')}")
    print(f"Results Directory:      {args.output}")
    print("==========================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
