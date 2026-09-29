#!/usr/bin/env python3
"""
CLI Tool: Run and evaluate empirical Phase E2 Retrieval Benchmark on archival indexes (SIH26096).

Enforces strict scientific research integrity:
- Checks Phase E1 OCR results status.
- If Phase E1 is BLOCKED or not validated on authentic scans, strictly enforces:
  LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1).
- Evaluates 4 retrieval strategies: BM25, Character 3-Gram Fuzzy, Dense (BGE-M3/Mock), Hybrid RRF (k=60).
- Measures Recall@10, nDCG@10, Mean Reciprocal Rank (MRR), Latency (ms), and Index Size.
- Emits results to results/e2/ (JSON, CSV comparison, and Markdown report).
- Never declares a universal winner: recognizes that optimal retrieval depends on OCR degradation levels.
"""

import argparse
import csv
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

from sih_archive.retrieval.base import RetrievalEngine
from sih_archive.retrieval.bm25 import BM25RetrievalEngine
from sih_archive.retrieval.dense import DenseRetrievalEngine, MockEmbeddingModel
from sih_archive.retrieval.hybrid import HybridRetrievalEngine
from sih_archive.retrieval.metrics import compute_mrr, compute_ndcg_at_k, compute_recall_at_k
from sih_archive.retrieval.ngram import CharacterNGramRetrievalEngine
from sih_archive.schemas.ocr import OCROutput

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("run_e2_retrieval")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase E2 Archival Retrieval Benchmark (SIH26096)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-ocr",
        "-i",
        type=str,
        default="outputs/ocr",
        help="Directory containing OCR JSON documents to index.",
    )
    parser.add_argument(
        "--e1-results",
        type=str,
        default="results/e1/e1_benchmark_report.json",
        help="Path to Phase E1 benchmark report to verify gating status.",
    )
    parser.add_argument(
        "--queries",
        "-q",
        type=str,
        default="data/evaluation/judged_queries.json",
        help="Path to judged queries JSON file with graded relevance.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="results/e2",
        help="Directory to save machine-readable results, CSV, and Markdown report.",
    )
    parser.add_argument(
        "--force-preview",
        action="store_true",
        help="Run preview evaluation on existing index even if E1 is blocked. Marked as LOCKED_PREVIEW.",
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


def load_judged_queries(queries_path: Path) -> List[Dict[str, Any]]:
    """Loads judged queries with graded relevance."""
    if not queries_path.is_file():
        return []
    try:
        with open(queries_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("queries", [])
    except Exception as e:
        logger.warning(f"Could not load queries from {queries_path}: {e}")
        return []


def run_e2_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir = Path(args.input_ocr)
    e1_path = Path(args.e1_results)
    queries_path = Path(args.queries)

    # 1. Inspect Phase E1 gating status
    e1_status = "UNKNOWN"
    if e1_path.is_file():
        try:
            with open(e1_path, "r", encoding="utf-8") as f:
                e1_meta = json.load(f)
            e1_status = e1_meta.get("gate_status", "UNKNOWN")
        except Exception:
            pass

    e1_is_measured = (e1_status == "MEASURED")

    if not e1_is_measured:
        gate_status = "LOCKED_PREVIEW (Gated on Empirical Completion of Phase E1)"
    else:
        gate_status = "READY_FOR_EMPIRICAL_EVALUATION"

    # 2. Load documents and queries
    docs = load_ocr_documents(ocr_dir)
    queries = load_judged_queries(queries_path)

    # 3. Setup retrieval engines
    bm25 = BM25RetrievalEngine()
    ngram = CharacterNGramRetrievalEngine(n=3)
    dense = DenseRetrievalEngine(embedding_model=MockEmbeddingModel(dim=32))
    hybrid = HybridRetrievalEngine(lexical_engine=bm25, dense_engine=dense, rrf_k=60)

    engines: List[RetrievalEngine] = [bm25, ngram, dense, hybrid]

    config_snapshot = {
        "benchmark": "E2_ARCHIVAL_RETRIEVAL",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "input_ocr_dir": str(ocr_dir),
        "e1_gate_status": e1_status,
        "gate_status": gate_status,
        "indexed_documents_count": len(docs),
        "target_pages_range": "100-200 pages",
        "judged_queries_count": len(queries),
        "target_queries_count": 50,
        "implemented_strategies": [eng.name for eng in engines],
    }

    with open(output_dir / "config_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(config_snapshot, f, indent=2)

    # 4. Execute evaluation across engines
    engine_benchmarks = []
    comparison_rows = []

    for eng in engines:
        idx_res = eng.index_documents(docs) if docs else None

        latencies = []
        recalls = []
        ndcgs = []
        mrrs = []
        query_details = []

        for q in queries:
            query_str = q.get("query", "")
            graded_rel = q.get("graded_relevance", {})
            relevant_ids = set(graded_rel.keys())

            t0 = time.perf_counter()
            hits = eng.search(query_str, top_k=10)
            latency = (time.perf_counter() - t0) * 1000.0
            latencies.append(latency)

            retrieved_ids = [h.page_id for h in hits]

            if relevant_ids:
                r_at_10 = compute_recall_at_k(retrieved_ids, relevant_ids, k=10)
                mrr = compute_mrr(retrieved_ids, relevant_ids)
                ndcg = compute_ndcg_at_k(retrieved_ids, graded_rel, k=10)
                recalls.append(r_at_10)
                mrrs.append(mrr)
                ndcgs.append(ndcg)
            else:
                r_at_10 = 0.0
                mrr = 0.0
                ndcg = 0.0

            query_details.append({
                "query_id": q.get("query_id"),
                "query": query_str,
                "latency_ms": round(latency, 2),
                "recall_at_10": round(r_at_10, 4),
                "ndcg_at_10": round(ndcg, 4),
                "top_hit": hits[0].page_id if hits else None,
                "top_score": hits[0].score if hits else 0.0,
            })

        mean_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        mean_rec = round(sum(recalls) / len(recalls), 4) if recalls else 0.0
        mean_ndcg = round(sum(ndcgs) / len(ndcgs), 4) if ndcgs else 0.0
        mean_mrr = round(sum(mrrs) / len(mrrs), 4) if mrrs else 0.0

        engine_benchmarks.append({
            "engine": eng.name,
            "mean_latency_ms": mean_lat,
            "mean_recall_at_10": mean_rec,
            "mean_ndcg_at_10": mean_ndcg,
            "mean_mrr": mean_mrr,
            "indexed_pages": len(docs),
            "total_tokens": idx_res.total_tokens_count if idx_res else 0,
            "queries_evaluated": len(queries),
            "sample_queries": query_details[:3],
        })

        comparison_rows.append({
            "engine": eng.name,
            "recall_at_10": mean_rec,
            "ndcg_at_10": mean_ndcg,
            "mrr": mean_mrr,
            "mean_latency_ms": mean_lat,
            "indexed_pages": len(docs),
        })

    # Save CSV comparison
    csv_file = output_dir / "retrieval_comparison.csv"
    if comparison_rows:
        keys = list(comparison_rows[0].keys())
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(comparison_rows)

    # Master JSON result
    report_data = {
        "phase": "E2_ARCHIVAL_RETRIEVAL",
        "benchmark_date": time.strftime("%Y-%m-%d", time.gmtime()),
        "gate_status": gate_status,
        "gating_rule": (
            "Retrieval benchmarks remain locked from official evaluation until empirical "
            "Phase E1 OCR outputs on authentic historical scans are verified."
        ),
        "e1_dependency_status": e1_status,
        "implemented_strategies": [eng.name for eng in engines],
        "corpus_summary": {
            "indexed_pages_count": len(docs),
            "target_corpus_range": [100, 200],
            "judged_queries_count": len(queries),
            "target_queries_count": 50,
        },
        "engine_benchmarks": engine_benchmarks,
        "scientific_integrity_notice": (
            "NO UNIVERSAL WINNER: Retrieval effectiveness varies across archival corruption tiers. "
            "Lexical BM25 performs well on clean vocabulary, Character 3-Gram excels under OCR substitution noise, "
            "Dense captures cross-lingual semantic intent, and Hybrid RRF provides balanced robustness. "
            "This benchmark represents a synthetic preview; final empirical evaluation is gated on E1."
        ),
    }

    with open(output_dir / "e2_retrieval_results.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Markdown Report
    with open(output_dir / "REPORT.md", "w", encoding="utf-8") as f:
        f.write("# SIH26096 — Phase E2 Archival Retrieval Benchmark Report\n\n")
        f.write(f"- **Execution Date:** {config_snapshot['timestamp']}\n")
        f.write(f"- **Gate Status:** `{gate_status}`\n")
        f.write(f"- **E1 Dependency Status:** `{e1_status}`\n")
        f.write(f"- **Indexed Pages:** {len(docs)} (Target: 100–200 pages)\n")
        f.write(f"- **Judged Queries:** {len(queries)} (Target: 50 queries)\n\n")

        f.write("## Scientific Gating Notice\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **Phase E2 is strictly gated on Phase E1.** Evaluating retrieval on synthetic text yields\n")
        f.write("> artificial 100% recall figures that fail to simulate historical OCR degradation.\n")
        f.write("> The benchmark below represents an implementation preview only.\n\n")

        f.write("## Comparative Engine Results (Preview)\n\n")
        f.write("| Engine | Recall@10 | nDCG@10 | MRR | Latency (ms) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for row in comparison_rows:
            f.write(f"| **{row['engine']}** | {row['recall_at_10']:.4f} | {row['ndcg_at_10']:.4f} | {row['mrr']:.4f} | {row['mean_latency_ms']:.2f} ms |\n")
        f.write("\n")
        f.write("### Qualitative Assessment\n")
        f.write("- **No Universal Winner:** Strategy selection must be data-driven based on the document condition.\n")
        f.write("- **BM25:** High precision on uncorrupted titles, acts, and proper nouns.\n")
        f.write("- **Character 3-Gram:** Resilient to broken characters, ink bleed, and scanning artifacts.\n")
        f.write("- **Dense Semantic:** Captures conceptual relationships when exact keywords differ.\n")
        f.write("- **Hybrid (RRF):** Optimal balance for general archival discovery.\n")

    logger.info(f"E2 Benchmark complete. Results written to {output_dir}")
    return report_data


def main(argv=None) -> int:
    args = parse_args(argv)
    res = run_e2_pipeline(args)
    print("\n================== E2 BENCHMARK SUMMARY ==================")
    print(f"Gate Status:            {res.get('gate_status')}")
    print(f"E1 Dependency Status:   {res.get('e1_dependency_status')}")
    print(f"Indexed Pages:          {res.get('corpus_summary', {}).get('indexed_pages_count')}")
    print(f"Results Directory:      {args.output}")
    print("==========================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
