#!/usr/bin/env python3
"""
CLI Tool: Run and compile machine-readable benchmark results for E1, E2, and E3 (SIH26096 Tasks 2-4).

Produces:
- results/e1_ocr_results.json
- results/e2_retrieval_results.json
- results/e3_attribution_results.json
"""

import argparse
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sih_archive.attribution.evaluator import AttributionEvaluator
from sih_archive.attribution.pipeline import EvidenceGroundedAnswerPipeline
from sih_archive.ocr.base import OCRAdapter
from sih_archive.ocr.tesseract import TesseractAdapter
from sih_archive.retrieval.bm25 import BM25RetrievalEngine
from sih_archive.retrieval.dense import DenseRetrievalEngine, MockEmbeddingModel
from sih_archive.retrieval.hybrid import HybridRetrievalEngine
from sih_archive.retrieval.metrics import compute_mrr, compute_ndcg_at_k, compute_recall_at_k
from sih_archive.retrieval.ngram import CharacterNGramRetrievalEngine
from sih_archive.schemas.ocr import OCROutput

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_e1_results(results_dir: Path) -> Path:
    """Compiles machine-readable E1 OCR benchmark results."""
    metrics_dir = repo_root / "outputs" / "metrics"
    ocr_dir = repo_root / "outputs" / "ocr"
    
    tess_adapter = TesseractAdapter()
    tess_avail, tess_msg = tess_adapter.is_available()

    # Load evaluated page metrics if available
    evaluated_pages = []
    summary_path = metrics_dir / "evaluation_summary.json"
    if summary_path.is_file():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                evaluated_pages = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read {summary_path}: {e}")

    # Build E1 record
    e1_data = {
        "phase": "E1_OCR",
        "benchmark_date": "2026-09-27",
        "gate_status": "BLOCKED_ON_HOST_OCR_BINARY" if not tess_avail else "READY_FOR_EMPIRICAL_RUN",
        "tesseract_host_status": {
            "available": tess_avail,
            "diagnostic_message": tess_msg,
            "supported_languages_target": ["eng", "hin", "mar"],
        },
        "research_integrity_notice": (
            "SYNTHETIC AND MOCK FIXTURE RESULTS MUST NOT BE REPORTED AS EMPIRICAL EVIDENCE OF "
            "HISTORICAL ARCHIVAL PERFORMANCE. Clean vector PDFs fail to model physical degradation."
        ),
        "corpus_metadata": {
            "document_id": "ambedkar_speech_vol1",
            "physical_classification": "Synthetic Digital Vector PDF Excerpt (5 pages)",
            "rights_status": "public",
            "rights_statute": "Indian Copyright Act 1957 Section 22 & Section 52(1)(q)",
        },
        "metrics_definition": {
            "CER": "Levenshtein character edit distance (S + D + I) / N_ref",
            "WER": "Levenshtein word edit distance (S_w + D_w + I_w) / N_w_ref",
            "reading_order_error": "1.0 - Normalized Kendall's Tau concordance",
            "region_box_recall": "True positive bounding boxes / Total reference regions at IoU >= 0.5",
        },
        "evaluated_pages_count": len([p for p in evaluated_pages if p.get("status") == "evaluated"]),
        "unannotated_pages_count": len([p for p in evaluated_pages if p.get("status") == "ground_truth_unavailable"]),
        "pages": evaluated_pages,
    }

    out_file = results_dir / "e1_ocr_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(e1_data, f, indent=2)
    logger.info(f"Generated E1 results: {out_file}")
    return out_file


def generate_e2_results(results_dir: Path) -> Path:
    """Compiles machine-readable E2 Retrieval benchmark results."""
    ocr_dir = repo_root / "outputs" / "ocr"
    ocr_files = sorted(ocr_dir.glob("*.json"))
    
    docs = []
    for f in ocr_files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if "regions" in data and "text" in data:
                docs.append(OCROutput.model_validate(data))
        except Exception:
            continue

    # Initialize engines
    bm25 = BM25RetrievalEngine()
    ngram = CharacterNGramRetrievalEngine(n=3)
    dense = DenseRetrievalEngine(embedding_model=MockEmbeddingModel(dim=32))
    hybrid = HybridRetrievalEngine(lexical_engine=bm25, dense_engine=dense, rrf_k=60)

    engines = [bm25, ngram, dense, hybrid]
    benchmark_queries = [
        {"query": "Castes in India Mechanism Genesis", "relevant_page_ids": {"ambedkar_speech_vol1_p0001"}},
        {"query": "Vasant Moon Education Department", "relevant_page_ids": {"ambedkar_speech_vol1_p0001"}},
        {"query": "Fundamental Rights Directive Principles", "relevant_page_ids": set()},
        {"query": "Annihilation of Caste Mahatma Gandhi", "relevant_page_ids": {"ambedkar_speech_vol1_p0002"}},
    ]

    engine_benchmarks = []
    for eng in engines:
        idx_res = eng.index_documents(docs) if docs else None
        
        q_results = []
        latencies = []
        recalls = []
        ndcgs = []
        mrrs = []

        for q in benchmark_queries:
            t0 = time.perf_counter()
            hits = eng.search(q["query"], top_k=10)
            latency = (time.perf_counter() - t0) * 1000.0
            latencies.append(latency)

            retrieved_ids = [h.page_id for h in hits]
            rel_set = q["relevant_page_ids"]

            if rel_set:
                r_at_10 = compute_recall_at_k(retrieved_ids, rel_set, k=10)
                mrr = compute_mrr(retrieved_ids, rel_set)
                ndcg = compute_ndcg_at_k(retrieved_ids, {pid: 3.0 for pid in rel_set}, k=10)
                recalls.append(r_at_10)
                mrrs.append(mrr)
                ndcgs.append(ndcg)

            q_results.append({
                "query": q["query"],
                "latency_ms": round(latency, 2),
                "top_hit_page_id": hits[0].page_id if hits else None,
                "top_hit_score": hits[0].score if hits else 0.0,
            })

        engine_benchmarks.append({
            "engine": eng.name,
            "mean_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "mean_recall_at_10": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
            "mean_ndcg_at_10": round(sum(ndcgs) / len(ndcgs), 4) if ndcgs else 0.0,
            "mean_mrr": round(sum(mrrs) / len(mrrs), 4) if mrrs else 0.0,
            "indexed_pages": idx_res.indexed_pages_count if idx_res else len(docs),
            "total_tokens": idx_res.total_tokens_count if idx_res else 0,
            "queries_evaluated": len(benchmark_queries),
            "sample_query_runs": q_results,
        })

    e2_data = {
        "phase": "E2_RETRIEVAL",
        "benchmark_date": "2026-09-27",
        "gate_status": "LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1)",
        "gating_rule": "Retrieval benchmarks remain locked from official evaluation until a real archival OCR corpus is verified.",
        "implemented_strategies": ["BM25", "Character 3-Gram Fuzzy", "Dense BGE-M3 (Mock)", "Hybrid RRF (k=60)"],
        "corpus_indexed_pages_count": len(docs),
        "engine_benchmarks": engine_benchmarks,
    }

    out_file = results_dir / "e2_retrieval_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(e2_data, f, indent=2)
    logger.info(f"Generated E2 results: {out_file}")
    return out_file


def generate_e3_results(results_dir: Path) -> Path:
    """Compiles machine-readable E3 Attribution benchmark results."""
    ocr_dir = repo_root / "outputs" / "ocr"
    ocr_files = sorted(ocr_dir.glob("*.json"))
    
    docs = []
    for f in ocr_files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if "regions" in data and "text" in data:
                docs.append(OCROutput.model_validate(data))
        except Exception:
            continue

    bm25 = BM25RetrievalEngine()
    pipeline = EvidenceGroundedAnswerPipeline(retrieval_engine=bm25, min_relevance_score=0.01, min_support_similarity=50.0)
    pipeline.register_documents(docs)

    test_queries = [
        {
            "question": "Who compiled Volume 1 of Dr. Ambedkar's Writings and Speeches?",
            "expected_page_id": "ambedkar_speech_vol1_p0001",
            "expected_span": "Compiled by Vasant Moon",
            "target_bbox": [208, 1070, 700, 100],
        },
        {
            "question": "What is the quantum mechanical spin of a neutral kaon meson?",
            "expected_page_id": None,  # Out of domain query -> Refusal expected
            "expected_span": "",
            "target_bbox": None,
        },
    ]

    answers = [pipeline.answer_question(q["question"]) for q in test_queries]
    evaluator = AttributionEvaluator()
    metrics = evaluator.evaluate_batch(answers, test_queries)

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

    e3_data = {
        "phase": "E3_ATTRIBUTION",
        "benchmark_date": "2026-09-27",
        "gate_status": "LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1 and E2)",
        "gating_rule": "Attribution scores remain locked from official evaluation until real archival OCR and retrieval inputs are validated.",
        "metrics": metrics.model_dump(),
        "attribution_chain": "Question -> Retrieval -> Page -> Region/BBox -> Claim -> Citation -> Viewer Target",
        "answers": answer_records,
    }

    out_file = results_dir / "e3_attribution_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(e3_data, f, indent=2)
    logger.info(f"Generated E3 results: {out_file}")
    return out_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile machine-readable benchmark results for E1, E2, and E3 (SIH26096)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="results",
        help="Directory to save machine-readable JSON results.",
    )
    args = parser.parse_args(argv)

    results_dir = Path(args.output_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Compiling Machine-Readable Benchmark Results ===")
    generate_e1_results(results_dir)
    generate_e2_results(results_dir)
    generate_e3_results(results_dir)
    print(f"All benchmark results successfully written to '{results_dir}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
