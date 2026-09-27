#!/usr/bin/env python3
"""
CLI Tool: Ingest archival documents into repository with provenance and rights audit (SIH26096 Task 1).

Accepts:
- PDF or page images
- Language and script metadata
- Source, institutional, and provenance metadata
- Rights status and statutory evidence
- Optional human ground-truth transcript

Usage Example:
    python scripts/ingest.py \
        --file path/to/document.pdf \
        --document-id ambedkar_speech_vol1 \
        --title "Dr. Babasaheb Ambedkar: Writings and Speeches, Vol. 1" \
        --source-organization "Dr. Ambedkar Foundation" \
        --language eng --script Latn \
        --rights-status public \
        --rights-evidence "Indian Copyright Act 1957 Section 52(1)(q)" \
        --ground-truth path/to/transcript.txt
"""

import argparse
import json
import logging
from pathlib import Path
import shutil
import sys
from typing import Optional

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pymupdf  # PyMuPDF
from sih_archive.ingestion.protocol import (
    audit_intake,
    check_rights_hygiene,
    create_manifest,
    save_manifest,
    validate_manifest,
)
from sih_archive.schemas.evaluation import GroundTruthPage
from sih_archive.schemas.manifest import DocumentManifest, RightsStatus

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archival Document Ingestion & Rights Intake CLI (SIH26096 Task 1)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--file",
        "-f",
        required=True,
        type=str,
        help="Path to input PDF or document image file to ingest into data/raw/.",
    )
    parser.add_argument(
        "--document-id",
        "-d",
        required=True,
        type=str,
        help="Unique alphanumeric document ID (e.g. 'ambedkar_speech_vol1').",
    )
    parser.add_argument(
        "--title",
        "-t",
        required=True,
        type=str,
        help="Full human-readable title of archival document.",
    )
    parser.add_argument(
        "--source-organization",
        "-s",
        required=True,
        type=str,
        help="Custodial institution, archive, or department (e.g. 'Dr. Ambedkar Foundation').",
    )
    parser.add_argument(
        "--source-url",
        "-u",
        type=str,
        default=None,
        help="Authoritative URL or catalogue link for source record.",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default="eng",
        help="ISO 639-3 three-letter lowercase language code (e.g. 'eng', 'mar', 'hin').",
    )
    parser.add_argument(
        "--script",
        type=str,
        default=None,
        help="ISO 15924 four-letter script code (e.g. 'Latn', 'Deva'). Defaults to Latn for eng, Deva for hin/mar.",
    )
    parser.add_argument(
        "--rights-status",
        "-r",
        type=str,
        default="public",
        choices=["public", "verified", "restricted", "unknown"],
        help="Intellectual property classification.",
    )
    parser.add_argument(
        "--rights-evidence",
        "-e",
        type=str,
        default=None,
        help="Statutory citation, custodial clearance memo, or public license reference.",
    )
    parser.add_argument(
        "--page-count",
        type=int,
        default=None,
        help="Page count (automatically extracted if PDF).",
    )
    parser.add_argument(
        "--ground-truth",
        "-g",
        type=str,
        default=None,
        help="Optional path to human reference transcript text file or GroundTruthPage JSON.",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Bibliographic notes, scan quality notes, or edition history.",
    )
    return parser.parse_args(argv)


def determine_default_script(language: str) -> str:
    lang = language.lower().strip()
    if lang in ("hin", "mar", "san"):
        return "Deva"
    return "Latn"


def main(argv=None) -> int:
    args = parse_args(argv)
    input_file = Path(args.file).resolve()

    if not input_file.is_file():
        logger.error(f"Input file not found: {input_file}")
        return 1

    script = args.script or determine_default_script(args.language)

    # Determine destination in data/raw/
    raw_dir = repo_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest_file = raw_dir / f"{args.document_id}{input_file.suffix}"

    # Copy to data/raw/ if not already there
    if input_file != dest_file.resolve():
        logger.info(f"Copying '{input_file.name}' to '{dest_file}'...")
        shutil.copy2(input_file, dest_file)

    # Compute page count
    page_count = args.page_count
    if page_count is None:
        if dest_file.suffix.lower() == ".pdf":
            try:
                doc = pymupdf.open(str(dest_file))
                page_count = len(doc)
                doc.close()
            except Exception as e:
                logger.error(f"Failed to read PDF page count from {dest_file}: {e}")
                return 1
        else:
            page_count = 1

    # Require rights evidence for public and verified
    rights_evidence = args.rights_evidence
    if args.rights_status in ("public", "verified") and not rights_evidence:
        logger.error(f"Rights status '{args.rights_status}' requires --rights-evidence.")
        return 1

    # Create manifest
    manifest_dir = repo_root / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{args.document_id}.json"

    rel_local_path = str(dest_file.relative_to(repo_root)).replace("\\", "/")

    try:
        manifest = create_manifest(
            document_id=args.document_id,
            title=args.title,
            source_organization=args.source_organization,
            source_url=args.source_url,
            language=args.language,
            script=script,
            rights_status=args.rights_status,
            rights_evidence=rights_evidence or "Pending verification",
            local_path=rel_local_path,
            page_count=page_count,
            notes=args.notes,
            repo_root=repo_root,
        )
        saved_manifest_path = save_manifest(manifest, output_dir=manifest_dir)
    except Exception as e:
        logger.error(f"Failed to create manifest: {e}")
        return 1

    # Ingest ground truth if provided
    if args.ground_truth:
        gt_path = Path(args.ground_truth).resolve()
        if not gt_path.is_file():
            logger.error(f"Ground truth file not found: {gt_path}")
            return 1

        gt_dir = repo_root / "data" / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)

        page_id = f"{args.document_id}_p0001"
        target_gt_json = gt_dir / f"{page_id}.json"

        if gt_path.suffix.lower() == ".json":
            # Validate JSON against GroundTruthPage
            try:
                with open(gt_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                gt_obj = GroundTruthPage.model_validate(data)
                gt_obj.to_json_file(target_gt_json)
                logger.info(f"Ingested verified GroundTruthPage JSON to '{target_gt_json.name}'.")
            except Exception as e:
                logger.error(f"Invalid GroundTruthPage JSON: {e}")
                return 1
        else:
            # Plain text file
            with open(gt_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            gt_obj = GroundTruthPage(
                document_id=args.document_id,
                page_id=page_id,
                reference_text=text_content,
                language=args.language,
                script=script,
                annotator="Archival Ingestion Specialist",
                verification_status="verified",
                notes=f"Transcript ingested from '{gt_path.name}'.",
                regions=[],
            )
            gt_obj.to_json_file(target_gt_json)
            logger.info(f"Ingested text transcript to '{target_gt_json.name}'.")

    # Perform formal intake audit
    audit_report = audit_intake(repo_root=repo_root, manifest_dir=manifest_dir, raw_dir=raw_dir)

    print("\n==================== INGESTION SUMMARY ====================")
    print(f"Document ID:   {manifest.document_id}")
    print(f"Title:         {manifest.title}")
    print(f"Local Path:    {manifest.local_path}")
    print(f"SHA-256:       {manifest.checksum_sha256}")
    print(f"Language:      {manifest.language} ({manifest.script})")
    print(f"Rights Status: {manifest.rights_status}")
    print(f"Evidence:      {manifest.rights_evidence}")
    print(f"Page Count:    {manifest.page_count}")
    print(f"Manifest:      {manifest_path}")
    print(f"Intake Audit:  Total {audit_report['total_manifests']} manifests ({audit_report['ready_for_benchmark_count']} ready for benchmark, hygiene compliance: {audit_report['hygiene_compliance']})")
    print("===========================================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
