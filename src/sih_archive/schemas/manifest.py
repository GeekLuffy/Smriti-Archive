"""Pydantic schema for archival document intake manifests (Phase E0).

Enforces intellectual property and rights hygiene, verifiable provenance,
and cryptographic integrity for archival documents.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RightsStatus = Literal["unknown", "verified", "restricted", "public"]


class DocumentManifest(BaseModel):
    """Archival Document Intake Manifest Schema.
    
    Tracks document metadata, custodial provenance, legal rights classification,
    local storage path, page count, and cryptographic hash.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    document_id: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        min_length=3,
        max_length=64,
        description="Unique identifier for the archival document (alphanumeric, hyphens, underscores).",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Full human-readable title of the document or volume.",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Authoritative online repository or archive URL (None if sourced offline).",
    )
    source_organization: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Custodial or publishing organization (e.g., Dr. Ambedkar Foundation, National Archives of India).",
    )
    language: str = Field(
        ...,
        pattern=r"^[a-z]{3}$",
        description="ISO 639-3 three-letter lowercase language code (e.g., 'eng', 'mar', 'hin').",
    )
    script: str = Field(
        ...,
        pattern=r"^[A-Z][a-z]{3}$",
        description="ISO 15924 four-letter script code (e.g., 'Latn', 'Deva').",
    )
    rights_status: RightsStatus = Field(
        ...,
        description="Legal rights category: 'unknown', 'verified', 'restricted', or 'public'.",
    )
    rights_evidence: Optional[str] = Field(
        default=None,
        description="Citation of statutory provision, fair dealing clause, license URL, or custodial clearance.",
    )
    local_path: str = Field(
        ...,
        description="Relative path from workspace root to the raw asset in data/raw/ (e.g., 'data/raw/ambedkar_vol01.pdf').",
    )
    page_count: int = Field(
        ...,
        ge=1,
        description="Total number of pages in the document (must be >= 1).",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Curatorial notes on physical condition, binding, scan artifacts, edition history.",
    )
    checksum_sha256: Optional[str] = Field(
        default=None,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="Hex-encoded SHA-256 cryptographic digest of the raw asset.",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of manifest registration.",
    )

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, v: str) -> str:
        """Ensure document_id is safe for filesystem operations and contains no path traversal."""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("document_id must not contain path traversal characters ('..', '/', '\\').")
        return v

    @field_validator("local_path")
    @classmethod
    def validate_local_path(cls, v: str) -> str:
        """Enforce that the local raw file path resides inside data/raw/ without path traversal."""
        norm = v.replace("\\", "/")
        if ".." in norm:
            raise ValueError("local_path must not contain directory traversal sequences ('..').")
        if not norm.startswith("data/raw/"):
            raise ValueError(f"local_path must reside within 'data/raw/'. Found: {v}")
        return norm

    @model_validator(mode="after")
    def validate_rights_evidence(self) -> "DocumentManifest":
        """Enforce that documents claimed as 'verified' or 'public' provide non-empty rights evidence."""
        if self.rights_status in ("verified", "public"):
            if not self.rights_evidence or not self.rights_evidence.strip():
                raise ValueError(
                    f"Documents with rights_status '{self.rights_status}' must include non-empty 'rights_evidence'."
                )
        return self

    def compute_sha256(self, repo_root: Path | str = ".") -> str:
        """Computes the SHA-256 checksum of the local raw file.
        
        Args:
            repo_root: Root directory of the repository.
            
        Returns:
            Lowercase hex-encoded SHA-256 digest string.
            
        Raises:
            FileNotFoundError: If the target file does not exist at repo_root / local_path.
        """
        root = Path(repo_root)
        target = root / self.local_path
        if not target.is_file():
            raise FileNotFoundError(f"Raw document asset not found at: {target}")
        hasher = hashlib.sha256()
        with open(target, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest().lower()

    def verify_integrity(self, repo_root: Path | str = ".") -> bool:
        """Verifies that the target file exists and matches the stored SHA-256 digest.
        
        Args:
            repo_root: Root directory of the repository.
            
        Returns:
            True if file exists and hash matches checksum_sha256. False otherwise.
        """
        if not self.checksum_sha256:
            return False
        try:
            computed = self.compute_sha256(repo_root)
            return computed.lower() == self.checksum_sha256.lower()
        except FileNotFoundError:
            return False

    def to_json_file(self, file_path: Path | str) -> Path:
        """Serializes the manifest to a formatted UTF-8 JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
        return path

    @classmethod
    def from_json_file(cls, file_path: Path | str) -> "DocumentManifest":
        """Deserializes a manifest from a JSON file.
        
        Args:
            file_path: Path to the JSON manifest.
            
        Returns:
            Validated DocumentManifest instance.
            
        Raises:
            FileNotFoundError: If file_path does not exist.
            ValueError / ValidationError: If JSON content fails schema validation.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Manifest file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())

    def to_dict(self) -> Dict[str, Any]:
        """Returns the manifest fields as a Python dictionary."""
        return self.model_dump()
