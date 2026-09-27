#!/usr/bin/env python3
"""
CLI Tool: Run modular OCR adapters on archival page images.

Usage Examples:
    python scripts/run_ocr.py --input data/processed/pages/ --engine mock --output outputs/ocr/
    python scripts/run_ocr.py -i data/processed/pages/ambedkar_speech_vol1_p0001.png -e mock -l eng
    python scripts/run_ocr.py -i data/processed/pages/ -e tesseract
"""

import argparse
from pathlib import Path
import sys
from typing import List

# Ensure src is in python path if run as standalone script
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sih_archive.ocr.base import OCRAdapter
from sih_archive.ocr.mock import MockOCRAdapter
from sih_archive.ocr.tesseract import TesseractAdapter
from sih_archive.preprocessing.filters import PreprocessingPipeline
from sih_archive.schemas.ocr import OCROutput


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Common OCR Adapter Execution Engine (SIH26096 Requirement R3)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=str,
        help="Path to input image file or directory containing page images.",
    )
    parser.add_argument(
        "--engine",
        "-e",
        type=str,
        default="tesseract",
        choices=["tesseract", "mock"],
        help="OCR engine adapter to execute ('tesseract' or 'mock').",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default="eng",
        help="ISO 639-3 language code for OCR engine (e.g. 'eng', 'mar', 'hin').",
    )
    parser.add_argument(
        "--preprocess",
        "-p",
        type=str,
        default="raw",
        help="Preprocessing filter pipeline identifier applied to image (e.g. 'raw', 'clahe', 'otsu').",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="outputs/ocr",
        help="Directory to save standardized OCR JSON output records.",
    )
    parser.add_argument(
        "--pages",
        type=str,
        default=None,
        help="Optional page ID pattern or filter substring (e.g. 'p0001' or 'p0001,p0002').",
    )
    parser.add_argument(
        "--tesseract-cmd",
        type=str,
        default=None,
        help="Explicit path to Tesseract binary executable.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Maximum timeout in seconds per page before raising or logging timeout.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Re-execute OCR and overwrite existing output JSON files.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check engine availability and diagnostics without processing images.",
    )
    return parser.parse_args(argv)


def get_image_files(input_path: Path, page_filter: str = None) -> List[Path]:
    """Collects target image files based on path and optional filter."""
    if input_path.is_file():
        return [input_path]

    if not input_path.is_dir():
        return []

    valid_exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    candidates = [
        p for p in sorted(input_path.iterdir())
        if p.is_file() and p.suffix.lower() in valid_exts and not p.name.startswith(".")
    ]

    if not page_filter:
        return candidates

    filter_terms = [t.strip().lower() for t in page_filter.split(",") if t.strip()]
    filtered = []
    for p in candidates:
        stem_lower = p.stem.lower()
        if any(term in stem_lower for term in filter_terms):
            filtered.append(p)
    return filtered


def main(argv=None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input)

    # Initialize selected adapter
    adapter: OCRAdapter
    if args.engine == "tesseract":
        adapter = TesseractAdapter(tesseract_cmd=args.tesseract_cmd)
    elif args.engine == "mock":
        adapter = MockOCRAdapter()
    else:
        print(f"ERROR: Unknown OCR engine: {args.engine}", file=sys.stderr)
        return 1

    # Check engine availability
    is_avail, avail_msg = adapter.is_available()

    if args.check_only:
        print(f"=== OCR Engine Diagnostics ===")
        print(f"Engine:    {args.engine}")
        print(f"Available: {is_avail}")
        print(f"Details:   {avail_msg}")
        return 0 if is_avail else 1

    if not is_avail:
        print("\n==================== OCR ENGINE DIAGNOSTIC ERROR ====================", file=sys.stderr)
        print(f"Engine '{args.engine}' is unavailable.", file=sys.stderr)
        print(f"Diagnostic: {avail_msg}", file=sys.stderr)
        print("=====================================================================\n", file=sys.stderr)
        return 1

    if not input_path.exists():
        print(f"ERROR: Input path not found: {input_path}", file=sys.stderr)
        return 1

    images = get_image_files(input_path, args.pages)
    if not images:
        print(f"ERROR: No matching images found at: {input_path}", file=sys.stderr)
        return 1

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== SIH26096 Common OCR Execution Engine ===")
    print(f"Engine:       {args.engine} ({adapter.get_version()})")
    print(f"Language:     {args.language}")
    print(f"Preprocess:   {args.preprocess}")
    print(f"Images:       {len(images)} target page(s)")
    print(f"Output Dir:   {out_dir}")
    print(f"Force Mode:   {args.force}")

    # Initialize preprocessing pipeline
    try:
        pipeline = PreprocessingPipeline.from_spec(args.preprocess)
    except Exception as e:
        print(f"ERROR: Invalid preprocessing specification '{args.preprocess}': {e}", file=sys.stderr)
        return 1

    processed_count = 0
    cached_count = 0
    error_count = 0

    for img in images:
        page_id = img.stem
        # Standard filename with engine and preprocess variant
        primary_out = out_dir / f"{page_id}_{args.engine}_{args.preprocess}.json"
        engine_out = out_dir / f"{page_id}_{args.engine}.json"
        alias_out = out_dir / f"{page_id}.json"

        if not args.force and primary_out.is_file():
            print(f"  [CACHED] {page_id} -> already processed ({primary_out.name})")
            cached_count += 1
            continue

        try:
            input_img_for_ocr = img
            preproc_duration_ms = 0.0
            filter_names = [f.name for f in pipeline.filters] if pipeline.filters else [args.preprocess]

            if pipeline.filters:
                preproc_dir = Path("data/processed/preprocessed")
                preproc_dir.mkdir(parents=True, exist_ok=True)
                preproc_out_file = preproc_dir / f"{page_id}_{args.preprocess}.png"
                _, preproc_meta, preproc_out_file = pipeline.process_file(img, output_path=preproc_out_file)
                input_img_for_ocr = preproc_out_file
                preproc_duration_ms = float(preproc_meta.get("duration_ms", 0.0))

            ocr_res = adapter.process_image(
                image_path=input_img_for_ocr,
                language=args.language,
                options={
                    "dpi": 300,
                    "filters": filter_names,
                    "timeout_seconds": args.timeout,
                    "page_id": page_id,
                },
            )

            # Record filter names and combined duration in OCROutput.processing
            ocr_res.processing.filters = filter_names
            ocr_res.processing.duration_ms = round(ocr_res.processing.duration_ms + preproc_duration_ms, 2)
            ocr_res.image_path = str(img).replace("\\", "/")

            if ocr_res.status == "success":
                ocr_res.to_json_file(primary_out)
                ocr_res.to_json_file(engine_out)
                ocr_res.to_json_file(alias_out)
                token_count = len(ocr_res.regions)
                duration = ocr_res.processing.duration_ms
                print(f"  [OK]     {page_id} -> {token_count:3d} tokens ({duration:.1f}ms)")
                processed_count += 1
            else:
                print(f"  [FAILED] {page_id} -> {ocr_res.status}: {ocr_res.error_message}", file=sys.stderr)
                error_count += 1

        except Exception as e:
            print(f"  [ERROR]  {page_id} -> Unexpected error: {e}", file=sys.stderr)
            error_count += 1

    print("\nOCR Execution Summary:")
    print(f"  Total Images:    {len(images)}")
    print(f"  Successfully:    {processed_count}")
    print(f"  Cached/Skipped:  {cached_count}")
    print(f"  Failures/Errors: {error_count}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
