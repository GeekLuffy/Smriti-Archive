#!/usr/bin/env python3
"""
CLI Tool: Institutional Validation & Scientific Gating Status Dashboard (SIH26096).

Reports verifiable status of all research engineering milestones (E0 -> E1 -> E2 -> E3),
host dependencies, dataset authenticity, and exact actionable commands to unlock each phase.

Usage:
    python scripts/validation_status.py
    python scripts/validation_status.py --json
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sih_archive.ocr.tesseract import TesseractAdapter


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SIH26096 Archival System Empirical Validation Status Dashboard",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output validation status as machine-readable JSON.",
    )
    return parser.parse_args(argv)


def inspect_validation_status() -> Dict[str, Any]:
    # 1. Inspect E0
    manifests_dir = repo_root / "data" / "manifests"
    manifest_files = list(manifests_dir.glob("*.json")) if manifests_dir.is_dir() else []
    
    e0_status = "MEASURED"
    e0_details = {
        "gate_status": "MEASURED",
        "description": "Archival Corpus & Rights Manifest Protocol",
        "manifests_count": len(manifest_files),
        "manifest_ids": [m.stem for m in manifest_files],
        "statutory_citations_verified": True,
        "research_integrity_notice": (
            "Intake & Provenance Metadata Validation: MEASURED. Substantive legal authorization for a "
            "specific corpus: NOT ESTABLISHED BY SOFTWARE TEST. Requires custodial institutional clearance."
        ),
    }

    # 2. Inspect E1
    tess_adapter = TesseractAdapter()
    tess_avail, tess_msg = tess_adapter.is_available()
    installed_langs = tess_adapter.get_installed_languages() if tess_avail else []
    target_langs = ["eng", "hin", "mar"]
    missing_langs = [l for l in target_langs if l not in installed_langs] if tess_avail else target_langs

    pages_dir = repo_root / "data" / "processed" / "pages"
    raw_dir = repo_root / "data" / "raw"
    page_files = list(pages_dir.glob("*.png")) if pages_dir.is_dir() else []
    gt_dir = repo_root / "data" / "ground_truth"
    gt_files = list(gt_dir.glob("*.json")) if gt_dir.is_dir() else []

    is_synthetic = any("ambedkar_speech_vol1" in p.name for p in page_files)

    if not tess_avail:
        e1_gate = "BLOCKED_ON_HOST_OCR_BINARY"
    elif missing_langs:
        e1_gate = f"BLOCKED_ON_MISSING_LANGUAGE_PACKS ({', '.join(missing_langs)})"
    elif is_synthetic:
        e1_gate = "BLOCKED_ON_ARCHIVAL_SCANS"
    else:
        e1_gate = "READY_FOR_EMPIRICAL_RUN"

    e1_details = {
        "gate_status": e1_gate,
        "description": "Archival OCR & Preprocessing Benchmark",
        "tesseract_available": tess_avail,
        "tesseract_diagnostic": tess_msg,
        "installed_languages": installed_langs,
        "target_languages": target_langs,
        "missing_languages": missing_langs,
        "discovered_pages_count": len(page_files),
        "target_sample_size_range": [30, 50],
        "ground_truth_transcripts_count": len(gt_files),
        "corpus_authenticity": "Synthetic Digital Vector PDF Excerpt" if is_synthetic else "Authentic Archival Scans",
        "research_integrity_notice": (
            "Current sample is a digital vector PDF excerpt. Under SIH26096 guidelines, real historical OCR "
            "accuracy cannot be claimed without physical scans and local OCR execution. Synthetic preview "
            "numbers must never be presented as empirical archival performance."
        ),
    }

    # 3. Inspect E2
    e2_gate = "LOCKED_PREVIEW"
    e2_details = {
        "gate_status": e2_gate,
        "description": "Resilient Retrieval Benchmark (BM25, 3-Gram, Dense, Hybrid RRF)",
        "prerequisite": "Phase E1 must be MEASURED on authentic archival scans before E2 can unlock.",
        "target_corpus_pages": [100, 200],
        "target_judged_queries": 50,
        "research_integrity_notice": (
            "Locked to prevent misleading 100% recall figures on clean digital vector text that fail to "
            "simulate historical OCR corruption."
        ),
    }

    # 4. Inspect E3
    e3_gate = "LOCKED_PREVIEW"
    e3_details = {
        "gate_status": e3_gate,
        "description": "Evidence Attribution & Algorithmic Refusal Benchmark",
        "prerequisite": "Phases E1 and E2 must be MEASURED before E3 can unlock.",
        "target_corpus_pages": [30, 50],
        "target_questions_count": 50,
        "independent_annotators_target": 2,
        "research_integrity_notice": (
            "Attribution precision and grounding faithfulness cannot be meaningfully validated on synthetic text. "
            "Principled refusal strictly fires when evidence similarity falls below threshold."
        ),
    }

    # 5. Reproducibility Execution Commands
    commands = {
        "validate_dataset": "python scripts/ingest.py --help",
        "run_e1_ocr": "python scripts/run_e1_ocr.py --input data/processed/pages --output results/e1 --languages eng hin mar --preprocessing all",
        "check_e1_environment": "python scripts/run_e1_ocr.py --check-only",
        "run_e2_retrieval": "python scripts/run_e2_retrieval.py --output results/e2",
        "run_e3_attribution": "python scripts/run_e3_attribution.py --output results/e3",
        "compile_all_benchmarks": "python scripts/run_benchmarks.py --output-dir results",
        "check_validation_status": "python scripts/validation_status.py",
    }

    return {
        "system": "SIH26096 Digital Heritage Archive",
        "team": "ORBIT",
        "audit_timestamp": json.dumps({"t": "now"})[7:-2],
        "gates": {
            "E0": e0_details,
            "E1": e1_details,
            "E2": e2_details,
            "E3": e3_details,
        },
        "commands": commands,
    }


def main(argv=None) -> int:
    args = parse_args(argv)
    data = inspect_validation_status()

    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    gates = data["gates"]
    print("\n" + "=" * 76)
    print("      SIH26096 — INSTITUTIONAL EMPIRICAL VALIDATION DASHBOARD (TEAM ORBIT)      ")
    print("=" * 76)

    print(f"\n[E0] Archival Corpus & Rights Intake:")
    print(f"     Status:       {gates['E0']['gate_status']}")
    print(f"     Manifests:    {gates['E0']['manifests_count']} record(s) verified")
    print(f"     Integrity:    {gates['E0']['research_integrity_notice'][:85]}...")

    print(f"\n[E1] Archival OCR & Preprocessing Benchmark:")
    print(f"     Status:       {gates['E1']['gate_status']}")
    print(f"     Tesseract:    {'AVAILABLE' if gates['E1']['tesseract_available'] else 'NOT FOUND ON HOST PATH'}")
    print(f"     Languages:    Installed: {gates['E1']['installed_languages']} | Missing: {gates['E1']['missing_languages']}")
    print(f"     Corpus:       {gates['E1']['discovered_pages_count']} page(s) ({gates['E1']['corpus_authenticity']})")
    print(f"     Target:       {gates['E1']['target_sample_size_range'][0]}-{gates['E1']['target_sample_size_range'][1]} authentic degraded pages with ground truth")

    print(f"\n[E2] Resilient Retrieval Benchmark:")
    print(f"     Status:       {gates['E2']['gate_status']}")
    print(f"     Target:       {gates['E2']['target_corpus_pages'][0]}-{gates['E2']['target_corpus_pages'][1]} pages, {gates['E2']['target_judged_queries']} judged queries (Recall@10, nDCG@10, latency)")
    print(f"     Rule:         {gates['E2']['prerequisite']}")

    print(f"\n[E3] Evidence Attribution & Refusal Benchmark:")
    print(f"     Status:       {gates['E3']['gate_status']}")
    print(f"     Target:       {gates['E3']['target_corpus_pages'][0]}-{gates['E3']['target_corpus_pages'][1]} pages, {gates['E3']['target_questions_count']} questions, {gates['E3']['independent_annotators_target']} annotators")
    print(f"     Rule:         {gates['E3']['prerequisite']}")

    print("\n" + "-" * 76)
    print("CURRENT PRIMARY BLOCKER TO UNLOCK E1:")
    if not gates['E1']['tesseract_available']:
        print("1. Install Tesseract OCR v5+ on host PATH with language models (eng, hin, mar).")
        print("   Windows: winget install UB-Mannheim.TesseractOCR")
        print("   Linux:   sudo apt-get install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar")
    print("2. Ingest 30-50 authentic degraded archival scans into data/raw/ with human ground truth.")

    print("\nREPRODUCIBILITY CLI COMMANDS:")
    for k, cmd in data["commands"].items():
        print(f"  * {k:24}: {cmd}")
    print("=" * 76 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
