"""Archival intake and rights hygiene protocol (Phase E0).

Enforces intellectual property and rights hygiene, immutable raw asset handling,
and cryptographic provenance for historical archives under SIH26096.
Auto-downloading of unverified copyrighted materials is strictly prohibited.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from sih_archive.schemas.manifest import DocumentManifest, RightsStatus

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when an archival intake or rights violation occurs."""
    pass


class RightsHygieneError(IngestionError):
    """Raised when a document lacks required rights documentation or violates copyright policy."""
    pass


def validate_raw_file_location(local_path: Union[str, Path], repo_root: Union[str, Path] = ".") -> Path:
    """Verifies that a raw document asset strictly resides inside data/raw/ without traversal.
    
    Args:
        local_path: Relative or absolute path to the raw asset.
        repo_root: Root directory of the repository.
        
    Returns:
        Resolved Path to the raw asset.
        
    Raises:
        IngestionError: If the path traverses outside data/raw/.
    """
    root = Path(repo_root).resolve()
    raw_dir = (root / "data" / "raw").resolve()
    
    target = (root / local_path).resolve() if not Path(local_path).is_absolute() else Path(local_path).resolve()
    
    # Check that target is within raw_dir
    try:
        target.relative_to(raw_dir)
    except ValueError:
        raise IngestionError(
            f"Physical asset separation violation: raw file '{local_path}' must reside within '{raw_dir}'."
        )
    return target


def check_rights_hygiene(manifest: DocumentManifest) -> Dict[str, Any]:
    """Evaluates the rights hygiene of a document manifest.
    
    Strict rules:
    - 'public': Cleared for open benchmarking and redistribution; requires statutory or public domain evidence.
    - 'verified': Cleared with custodial authorization or explicit CC license; requires evidence.
    - 'restricted': In-copyright or restricted access; benchmarking permitted only in closed research mode; redistribution prohibited.
    - 'unknown': Unverified intake; flagged for audit; not cleared for public release or benchmark execution.
    
    Args:
        manifest: DocumentManifest instance.
        
    Returns:
        Dictionary with hygiene assessment details:
        - status: rights status string
        - cleared_for_benchmark: bool
        - allows_redistribution: bool
        - requires_rights_audit: bool
        - message: descriptive diagnostic
    """
    status = manifest.rights_status
    evidence = manifest.rights_evidence or ""

    if status == "public":
        return {
            "rights_status": status,
            "cleared_for_benchmark": True,
            "allows_redistribution": True,
            "requires_rights_audit": False,
            "evidence": evidence,
            "message": "Document is in public domain with cited statutory or public authority evidence.",
        }
    elif status == "verified":
        return {
            "rights_status": status,
            "cleared_for_benchmark": True,
            "allows_redistribution": False,
            "requires_rights_audit": False,
            "evidence": evidence,
            "message": "Document has verified custodial or institutional clearance for archival research.",
        }
    elif status == "restricted":
        return {
            "rights_status": status,
            "cleared_for_benchmark": True,
            "allows_redistribution": False,
            "requires_rights_audit": True,
            "evidence": evidence,
            "message": "Document is restricted/in-copyright; fair-dealing research benchmarking only; no redistribution.",
        }
    else:  # "unknown"
        return {
            "rights_status": status,
            "cleared_for_benchmark": False,
            "allows_redistribution": False,
            "requires_rights_audit": True,
            "evidence": evidence,
            "message": "Rights status is unknown. Document must undergo rights audit before inclusion in benchmarks.",
        }


def create_manifest(
    document_id: str,
    title: str,
    source_organization: str,
    language: str,
    script: str,
    rights_status: RightsStatus,
    local_path: str,
    page_count: int,
    source_url: Optional[str] = None,
    rights_evidence: Optional[str] = None,
    notes: Optional[str] = None,
    checksum_sha256: Optional[str] = None,
    auto_compute_checksum: bool = True,
    repo_root: Union[str, Path] = ".",
) -> DocumentManifest:
    """Creates, validates, and hashes an archival document manifest.
    
    Args:
        document_id: Unique document identifier (alphanumeric, -, _).
        title: Human-readable title.
        source_organization: Custodial or publishing institution.
        language: ISO 639-3 three-letter code.
        script: ISO 15924 four-letter code.
        rights_status: One of 'unknown', 'verified', 'restricted', 'public'.
        local_path: Path relative to repo root (must begin with data/raw/).
        page_count: Total pages in document (>= 1).
        source_url: Optional authoritative URL.
        rights_evidence: Statutory citation or custodial license (required for public/verified).
        notes: Optional curatorial notes.
        checksum_sha256: Optional precomputed hex SHA-256.
        auto_compute_checksum: If True and checksum_sha256 is None, computes hash from local file if present.
        repo_root: Repository root path.
        
    Returns:
        Validated DocumentManifest instance.
    """
    root = Path(repo_root)
    norm_local = local_path.replace("\\", "/")
    
    # If checksum not provided and file exists, compute it
    if checksum_sha256 is None and auto_compute_checksum:
        file_path = root / norm_local
        if file_path.is_file():
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            checksum_sha256 = hasher.hexdigest().lower()

    manifest = DocumentManifest(
        document_id=document_id,
        title=title,
        source_url=source_url,
        source_organization=source_organization,
        language=language,
        script=script,
        rights_status=rights_status,
        rights_evidence=rights_evidence,
        local_path=norm_local,
        page_count=page_count,
        notes=notes,
        checksum_sha256=checksum_sha256,
    )
    return manifest


def load_manifest(manifest_path: Union[str, Path]) -> DocumentManifest:
    """Loads and validates a DocumentManifest from a JSON file.
    
    Args:
        manifest_path: Path to the JSON manifest file.
        
    Returns:
        Validated DocumentManifest.
    """
    return DocumentManifest.from_json_file(manifest_path)


def save_manifest(
    manifest: DocumentManifest,
    output_dir: Union[str, Path] = "data/manifests",
) -> Path:
    """Saves a DocumentManifest to a standardized JSON file.
    
    Target path: {output_dir}/{manifest.document_id}.json
    
    Args:
        manifest: DocumentManifest instance.
        output_dir: Directory where the manifest will be stored.
        
    Returns:
        Path to the written JSON file.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target_path = out_dir / f"{manifest.document_id}.json"
    manifest.to_json_file(target_path)
    logger.info("Saved manifest %s to %s", manifest.document_id, target_path)
    return target_path


def validate_manifest(
    manifest: DocumentManifest,
    repo_root: Union[str, Path] = ".",
) -> Dict[str, Any]:
    """Validates manifest integrity, raw file presence, checksum match, and rights hygiene.
    
    Args:
        manifest: DocumentManifest instance.
        repo_root: Repository root path.
        
    Returns:
        Validation report dictionary:
        - document_id: str
        - is_valid: bool (schema valid and file location valid)
        - raw_file_exists: bool
        - raw_file_path: str
        - checksum_valid: Optional[bool] (None if no checksum stored or file missing)
        - rights_hygiene: Dict[str, Any]
        - ready_for_processing: bool
        - issues: List[str]
    """
    root = Path(repo_root)
    issues: List[str] = []
    
    # Check location constraint
    raw_file_valid_loc = True
    try:
        resolved_path = validate_raw_file_location(manifest.local_path, root)
    except IngestionError as e:
        raw_file_valid_loc = False
        issues.append(str(e))
        resolved_path = root / manifest.local_path

    # Check file existence
    file_exists = resolved_path.is_file()
    if not file_exists:
        issues.append(f"Raw file asset not found on disk at '{manifest.local_path}'.")

    # Check checksum
    checksum_valid: Optional[bool] = None
    if file_exists and manifest.checksum_sha256:
        checksum_valid = manifest.verify_integrity(root)
        if not checksum_valid:
            issues.append(
                f"Checksum mismatch: stored SHA-256 does not match file content at '{manifest.local_path}'."
            )
    elif file_exists and not manifest.checksum_sha256:
        issues.append("Raw file exists but no checksum_sha256 is recorded in manifest.")

    # Rights hygiene
    rights_hygiene = check_rights_hygiene(manifest)
    if rights_hygiene["requires_rights_audit"]:
        issues.append(
            f"Rights status is '{manifest.rights_status}': {rights_hygiene['message']}"
        )

    ready_for_processing = (
        raw_file_valid_loc
        and file_exists
        and (checksum_valid is not False)
        and rights_hygiene["cleared_for_benchmark"]
    )

    return {
        "document_id": manifest.document_id,
        "is_valid": len(issues) == 0 or (len(issues) == 1 and not file_exists),
        "raw_file_exists": file_exists,
        "raw_file_path": str(manifest.local_path),
        "checksum_valid": checksum_valid,
        "rights_hygiene": rights_hygiene,
        "ready_for_processing": ready_for_processing,
        "issues": issues,
    }


def discover_manifests(
    manifest_dir: Union[str, Path] = "data/manifests",
) -> List[DocumentManifest]:
    """Finds and parses all JSON manifests in a directory.
    
    Args:
        manifest_dir: Directory containing manifest JSON files.
        
    Returns:
        List of loaded DocumentManifest objects sorted by document_id.
    """
    m_dir = Path(manifest_dir)
    manifests: List[DocumentManifest] = []
    if not m_dir.is_dir():
        return manifests

    for path in sorted(m_dir.glob("*.json")):
        try:
            m = load_manifest(path)
            manifests.append(m)
        except Exception as e:
            logger.warning("Skipping invalid manifest at %s: %s", path, e)
    return manifests


def audit_intake(
    repo_root: Union[str, Path] = ".",
    manifest_dir: Union[str, Path] = "data/manifests",
    raw_dir: Union[str, Path] = "data/raw",
) -> Dict[str, Any]:
    """Audits the archival intake state across data/manifests/ and data/raw/.
    
    Detects unmanifested files, missing assets, rights breakdown, and readiness.
    
    Args:
        repo_root: Repository root path.
        manifest_dir: Manifests directory path.
        raw_dir: Raw files directory path.
        
    Returns:
        Audit report dictionary.
    """
    root = Path(repo_root)
    m_dir = (root / manifest_dir) if not Path(manifest_dir).is_absolute() else Path(manifest_dir)
    r_dir = (root / raw_dir) if not Path(raw_dir).is_absolute() else Path(raw_dir)

    manifests = discover_manifests(m_dir)
    manifest_map = {m.document_id: m for m in manifests}
    
    # Collect all physical files in raw_dir excluding .gitkeep
    raw_files: List[Path] = []
    if r_dir.is_dir():
        raw_files = [
            f for f in r_dir.rglob("*")
            if f.is_file() and f.name != ".gitkeep"
        ]

    # Map manifested files
    manifested_local_paths = {
        (root / m.local_path).resolve() for m in manifests
    }

    missing_raw_files: List[Dict[str, Any]] = []
    checksum_mismatches: List[str] = []
    rights_breakdown: Dict[str, int] = {"public": 0, "verified": 0, "restricted": 0, "unknown": 0}
    ready_count = 0

    for m in manifests:
        rights_breakdown[m.rights_status] = rights_breakdown.get(m.rights_status, 0) + 1
        res = validate_manifest(m, root)
        if not res["raw_file_exists"]:
            missing_raw_files.append({
                "document_id": m.document_id,
                "local_path": m.local_path,
            })
        if res["checksum_valid"] is False:
            checksum_mismatches.append(m.document_id)
        if res["ready_for_processing"]:
            ready_count += 1

    # Unmanifested raw files
    unmanifested_raw_files: List[str] = []
    for f in raw_files:
        if f.resolve() not in manifested_local_paths:
            unmanifested_raw_files.append(str(f.relative_to(root)).replace("\\", "/"))

    return {
        "total_manifests": len(manifests),
        "manifested_documents": [m.document_id for m in manifests],
        "total_raw_files": len(raw_files),
        "unmanifested_raw_files": unmanifested_raw_files,
        "missing_raw_files": missing_raw_files,
        "checksum_mismatches": checksum_mismatches,
        "rights_breakdown": rights_breakdown,
        "ready_for_benchmark_count": ready_count,
        "hygiene_compliance": len(unmanifested_raw_files) == 0 and len(checksum_mismatches) == 0,
    }
