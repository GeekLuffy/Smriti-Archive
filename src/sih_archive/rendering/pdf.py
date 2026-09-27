"""Deterministic PDF to Page Image Rendering Pipeline (Requirement R2)."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import warnings

# Suppress PyMuPDF fitz deprecation warning in modern pymupdf releases
warnings.filterwarnings("ignore", category=UserWarning, module="fitz")
try:
    import pymupdf as fitz
except ImportError:
    import fitz

from sih_archive.schemas.rendering import DocumentRenderingManifest, PageProvenance


def compute_sha256(file_path: Union[str, Path]) -> str:
    """Computes hex-encoded SHA-256 digest of a file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for SHA-256 calculation: {path}")
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_page_range(spec: Optional[Union[str, List[int], int]], total_pages: int) -> List[int]:
    """
    Parses page selection expressions into a sorted list of 1-indexed page integers.

    Supported expressions:
        - None or 'all': all pages [1..total_pages]
        - single int, e.g. 3
        - range, e.g. '1-5'
        - comma-separated list and ranges, e.g. '1,3,5-7'
    """
    if total_pages < 1:
        raise ValueError(f"Document must have at least 1 page, got {total_pages}.")

    if spec is None:
        return list(range(1, total_pages + 1))

    if isinstance(spec, int):
        if spec < 1 or spec > total_pages:
            raise ValueError(f"Page number {spec} out of range [1, {total_pages}].")
        return [spec]

    if isinstance(spec, (list, tuple)):
        pages = set()
        for p in spec:
            if not isinstance(p, int) or p < 1 or p > total_pages:
                raise ValueError(f"Page number {p} out of range [1, {total_pages}].")
            pages.add(p)
        return sorted(pages)

    spec_str = str(spec).strip().lower()
    if spec_str == "all" or not spec_str:
        return list(range(1, total_pages + 1))

    pages = set()
    parts = spec_str.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bounds = part.split("-", 1)
            try:
                start = int(bounds[0].strip())
                end = int(bounds[1].strip())
            except ValueError:
                raise ValueError(f"Malformed page range component: '{part}'.")
            if start < 1 or end > total_pages or start > end:
                raise ValueError(
                    f"Invalid range '{part}'. Document has {total_pages} pages (expected 1 <= start <= end <= {total_pages})."
                )
            pages.update(range(start, end + 1))
        else:
            try:
                p = int(part)
            except ValueError:
                raise ValueError(f"Invalid page number token: '{part}'.")
            if p < 1 or p > total_pages:
                raise ValueError(f"Page number {p} out of range [1, {total_pages}].")
            pages.add(p)

    if not pages:
        raise ValueError(f"Page specification '{spec}' resolved to empty page set.")

    return sorted(pages)


def get_pdf_metadata(pdf_path: Union[str, Path]) -> Dict[str, Any]:
    """Extracts document-level metadata and page count using PyMuPDF."""
    target = Path(pdf_path)
    if not target.is_file():
        raise FileNotFoundError(f"PDF document not found: {target}")

    doc = fitz.open(str(target))
    try:
        return {
            "page_count": len(doc),
            "format": doc.metadata.get("format", "PDF"),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "mod_date": doc.metadata.get("modDate", ""),
            "is_encrypted": doc.is_encrypted,
        }
    finally:
        doc.close()


def render_pdf(
    pdf_path: Union[str, Path],
    output_dir: Union[str, Path] = "data/processed/pages",
    dpi: int = 300,
    pages: Optional[Union[str, List[int], int]] = None,
    force: bool = False,
    document_id: Optional[str] = None,
) -> DocumentRenderingManifest:
    """
    Renders archival PDF pages into high-resolution PNG images with complete provenance.

    Parameters:
        pdf_path: Path to the source PDF file (or JSON manifest referencing the PDF).
        output_dir: Directory where PNG images and provenance manifests will be saved.
        dpi: Target resolution in dots per inch (default 300).
        pages: Page selection filter ('all', '1-5', '1,3,5', or list of ints).
        force: If True, overwrite existing rendered pages without checking cache.
        document_id: Optional document ID. If None, derived from manifest or filename stem.

    Returns:
        DocumentRenderingManifest containing all rendered page provenance records.
    """
    input_path = Path(pdf_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Check if input is a manifest JSON
    if input_path.suffix.lower() == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        if "local_path" in manifest_data:
            actual_pdf = Path(manifest_data["local_path"])
            if not actual_pdf.is_file():
                # Try relative to parent of manifest or workspace root
                possible = Path.cwd() / manifest_data["local_path"]
                if possible.is_file():
                    actual_pdf = possible
            input_path = actual_pdf
        if not document_id and "document_id" in manifest_data:
            document_id = manifest_data["document_id"]

    if dpi < 72 or dpi > 1200:
        raise ValueError(f"DPI must be between 72 and 1200, got {dpi}.")

    if not document_id:
        document_id = input_path.stem

    source_pdf_sha256 = compute_sha256(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(input_path))
    try:
        total_pages = len(doc)
        target_pages = parse_page_range(pages, total_pages)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        provenance_list: List[PageProvenance] = []
        rendered_count = 0

        for page_num in target_pages:
            page_idx = page_num - 1
            page_id = f"{document_id}_p{page_num:04d}"
            image_filename = f"{page_id}.png"
            image_path = out_dir / image_filename
            manifest_filename = f"{page_id}_manifest.json"
            manifest_path = out_dir / manifest_filename

            # Check duplicate rendering detection
            if not force and image_path.is_file() and manifest_path.is_file():
                try:
                    existing_prov = PageProvenance.from_json_file(manifest_path)
                    # Verify cache validity
                    if (
                        existing_prov.dpi == dpi
                        and existing_prov.source_pdf_sha256 == source_pdf_sha256
                        and existing_prov.page_number == page_num
                    ):
                        # Verify the physical image matches the recorded hash
                        current_img_sha = compute_sha256(image_path)
                        if current_img_sha.lower() == existing_prov.sha256.lower():
                            existing_prov.status = "cached"
                            provenance_list.append(existing_prov)
                            continue
                except Exception:
                    # In case of corrupted manifest, proceed to re-render
                    pass

            # Perform high-fidelity rasterization
            page = doc.load_page(page_idx)
            rect = page.rect
            orig_w = float(rect.width)
            orig_h = float(rect.height)
            rot = int(page.rotation)

            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(str(image_path))

            img_sha256 = compute_sha256(image_path)

            provenance = PageProvenance(
                document_id=document_id,
                page_id=page_id,
                page_number=page_num,
                width=pix.width,
                height=pix.height,
                orig_width_pt=orig_w,
                orig_height_pt=orig_h,
                rotation=rot,
                dpi=dpi,
                source_pdf=str(input_path).replace("\\", "/"),
                source_pdf_sha256=source_pdf_sha256,
                image_path=str(image_path).replace("\\", "/"),
                sha256=img_sha256,
                rendered_at=datetime.now(timezone.utc).isoformat(),
                status="rendered",
            )

            # Save individual page provenance manifests
            provenance.to_json_file(manifest_path)
            # Also save standard {page_id}.json alias for downstream tools
            alias_path = out_dir / f"{page_id}.json"
            provenance.to_json_file(alias_path)

            provenance_list.append(provenance)
            rendered_count += 1

        # Save document-level rendering manifest
        doc_manifest = DocumentRenderingManifest(
            document_id=document_id,
            source_pdf=str(input_path).replace("\\", "/"),
            source_pdf_sha256=source_pdf_sha256,
            dpi=dpi,
            total_pages_in_pdf=total_pages,
            rendered_pages_count=rendered_count,
            pages=provenance_list,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        doc_manifest_path = out_dir / f"{document_id}_rendered_manifest.json"
        doc_manifest.to_json_file(doc_manifest_path)

        return doc_manifest

    finally:
        doc.close()
