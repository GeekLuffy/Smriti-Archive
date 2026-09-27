#!/usr/bin/env python3
"""
CLI Tool: Render PDF to high-resolution page images with provenance manifests.

Usage Examples:
    python scripts/render_pdf.py --input data/raw/ambedkar_speech_vol1.pdf
    python scripts/render_pdf.py -i data/raw/ambedkar_speech_vol1.pdf -o data/processed/pages -d 300 -p 1-3
    python scripts/render_pdf.py -i data/manifests/ambedkar_speech_vol1.json --force
"""

import argparse
from pathlib import Path
import sys

# Ensure src is in python path if run as standalone script
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sih_archive.rendering.pdf import render_pdf, get_pdf_metadata


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministic PDF to Page Image Rendering Pipeline (SIH26096 Requirement R2)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=str,
        help="Path to input archival PDF or document manifest JSON.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/pages",
        help="Destination directory for rendered PNG page images and provenance manifests.",
    )
    parser.add_argument(
        "--dpi",
        "-d",
        type=int,
        default=300,
        help="Target rendering resolution in dots per inch (e.g. 300 for Tier 1 preservation).",
    )
    parser.add_argument(
        "--pages",
        "-p",
        type=str,
        default="all",
        help="Page selection expression: 'all', single number '3', range '1-5', or set '1,3,5-7'.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-rendering even if output images and valid manifests already exist.",
    )
    parser.add_argument(
        "--document-id",
        type=str,
        default=None,
        help="Explicit document identifier override (defaults to manifest id or filename stem).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        print(f"=== SIH26096 Archival PDF Rendering Pipeline ===")
        print(f"Input:       {input_path}")
        print(f"Output Dir:  {args.output}")
        print(f"Target DPI:  {args.dpi}")
        print(f"Page Spec:   {args.pages}")
        print(f"Force Mode:  {args.force}")

        manifest = render_pdf(
            pdf_path=input_path,
            output_dir=args.output,
            dpi=args.dpi,
            pages=args.pages,
            force=args.force,
            document_id=args.document_id,
        )

        print("\nRendering Summary:")
        print(f"  Document ID:     {manifest.document_id}")
        print(f"  Total Pages:     {manifest.total_pages_in_pdf}")
        print(f"  Rendered/Total:  {len(manifest.pages)} pages processed")
        print(f"  Newly Rendered:  {manifest.rendered_pages_count}")
        print(f"  Cached/Skipped:  {len(manifest.pages) - manifest.rendered_pages_count}")

        for page in manifest.pages:
            status_tag = "[NEW]" if page.status == "rendered" else "[CACHED]"
            print(f"    {status_tag} Page {page.page_number:02d} -> {page.page_id}.png ({page.width}x{page.height} px, sha256={page.sha256[:12]}...)")

        print(f"\nCompleted successfully. Provenance manifest written to {args.output}/{manifest.document_id}_rendered_manifest.json")
        return 0

    except Exception as e:
        print(f"ERROR: Rendering failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
