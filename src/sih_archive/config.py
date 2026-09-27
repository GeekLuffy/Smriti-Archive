"""
Configuration and Storage Architecture for SIH26096 Archive System.

Supports both local development environments and containerized cloud deployments
(such as Northflank) using persistent volume mounts and configurable environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def _resolve_repo_root() -> Path:
    """Finds repository root relative to this config file."""
    return Path(__file__).resolve().parent.parent.parent


def _default_data_dir() -> Path:
    return Path(os.environ.get("ARCHIVE_DATA_DIR", _resolve_repo_root() / "data")).resolve()


def _default_ground_truth_dir() -> Path:
    if "GROUND_TRUTH_DIR" in os.environ:
        return Path(os.environ["GROUND_TRUTH_DIR"]).resolve()
    return _default_data_dir() / "ground_truth"


def _default_manifests_dir() -> Path:
    if "MANIFESTS_DIR" in os.environ:
        return Path(os.environ["MANIFESTS_DIR"]).resolve()
    return _default_data_dir() / "manifests"


def _default_raw_dir() -> Path:
    if "RAW_DIR" in os.environ:
        return Path(os.environ["RAW_DIR"]).resolve()
    return _default_data_dir() / "raw"


def _default_processed_dir() -> Path:
    if "PROCESSED_DIR" in os.environ:
        return Path(os.environ["PROCESSED_DIR"]).resolve()
    return _default_data_dir() / "processed"


class ArchiveConfig(BaseModel):
    """Runtime configuration model driven by environment variables."""

    # Core Directories
    repo_root: Path = Field(default_factory=_resolve_repo_root)
    archive_data_dir: Path = Field(default_factory=_default_data_dir)
    ground_truth_dir: Path = Field(default_factory=_default_ground_truth_dir)
    manifests_dir: Path = Field(default_factory=_default_manifests_dir)
    raw_dir: Path = Field(default_factory=_default_raw_dir)
    processed_dir: Path = Field(default_factory=_default_processed_dir)
    results_dir: Path = Field(default_factory=lambda: Path(os.environ.get("RESULTS_DIR", _resolve_repo_root() / "results")).resolve())
    outputs_dir: Path = Field(default_factory=lambda: Path(os.environ.get("OUTPUTS_DIR", _resolve_repo_root() / "outputs")).resolve())
    model_cache_dir: Path = Field(default_factory=lambda: Path(os.environ.get("MODEL_CACHE_DIR", _resolve_repo_root() / "cache" / "models")).resolve())

    # Server / Northflank Port Binding
    host: str = Field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.environ.get("PORT", "8000")))
    app_env: str = Field(default_factory=lambda: os.environ.get("APP_ENV", "development"))
    app_debug: bool = Field(default_factory=lambda: os.environ.get("APP_DEBUG", "false").lower() in ("true", "1", "yes"))

    # Database / Metadata Store URL (configurable, decoupled)
    database_url: Optional[str] = Field(default_factory=lambda: os.environ.get("DATABASE_URL", None))

    # Security & Upload Limits
    cors_origins: List[str] = Field(
        default_factory=lambda: [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
    )
    is_vercel: bool = Field(default_factory=lambda: bool(os.environ.get("VERCEL")))
    max_upload_size_bytes: int = Field(
        default_factory=lambda: int(
            os.environ.get(
                "MAX_UPLOAD_SIZE_BYTES",
                str(4 * 1024 * 1024 if os.environ.get("VERCEL") else 50 * 1024 * 1024),
            )
        )
    )

    # Execution Mode (DEMO vs RESEARCH_VALIDATION)
    execution_mode: str = Field(
        default_factory=lambda: os.environ.get("EXECUTION_MODE", "DEMO").upper()
    )

    # Compute Device Configuration
    ocr_device: str = Field(
        default_factory=lambda: os.environ.get("OCR_DEVICE", "cpu").lower()
    )

    def ensure_directories(self) -> None:
        """Ensures all configured filesystem storage locations exist with proper permissions."""
        for d in [
            self.archive_data_dir,
            self.ground_truth_dir,
            self.manifests_dir,
            self.raw_dir,
            self.processed_dir,
            self.results_dir,
            self.outputs_dir,
            self.model_cache_dir,
        ]:
            try:
                d.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass

    def get_storage_status(self) -> Dict[str, Any]:
        """Audits writability and state of all persistent and generated storage directories."""
        status = {}
        dirs_to_check = {
            "archive_data_dir": self.archive_data_dir,
            "ground_truth_dir": self.ground_truth_dir,
            "manifests_dir": self.manifests_dir,
            "raw_dir": self.raw_dir,
            "processed_dir": self.processed_dir,
            "results_dir": self.results_dir,
            "outputs_dir": self.outputs_dir,
            "model_cache_dir": self.model_cache_dir,
        }
        for name, path in dirs_to_check.items():
            exists = path.is_dir()
            writable = False
            if exists:
                test_file = path / f".write_test_{os.getpid()}"
                try:
                    test_file.touch()
                    test_file.unlink()
                    writable = True
                except Exception:
                    writable = False
            status[name] = {
                "path": str(path),
                "exists": exists,
                "writable": writable,
            }
        return status

    def get_safe_diagnostics(self) -> Dict[str, Any]:
        """Returns non-sensitive configuration diagnostics for monitoring endpoints."""
        return {
            "app_env": self.app_env,
            "app_debug": self.app_debug,
            "host": self.host,
            "port": self.port,
            "execution_mode": self.execution_mode,
            "ocr_device": self.ocr_device,
            "is_vercel": self.is_vercel,
            "platform_mode": "vercel_serverless" if self.is_vercel else "docker_or_host",
            "max_upload_size_bytes": self.max_upload_size_bytes,
            "has_database_url": self.database_url is not None,
            "storage_paths": {
                "archive_data_dir": str(self.archive_data_dir),
                "ground_truth_dir": str(self.ground_truth_dir),
                "results_dir": str(self.results_dir),
                "outputs_dir": str(self.outputs_dir),
                "model_cache_dir": str(self.model_cache_dir),
            }
        }


# Singleton instance accessor
_settings: Optional[ArchiveConfig] = None


def get_config() -> ArchiveConfig:
    """Returns application configuration instance."""
    global _settings
    if _settings is None:
        _settings = ArchiveConfig()
        _settings.ensure_directories()
    return _settings


def reset_config() -> ArchiveConfig:
    """Resets cached configuration, re-evaluating environment variables."""
    global _settings
    _settings = ArchiveConfig()
    _settings.ensure_directories()
    return _settings
