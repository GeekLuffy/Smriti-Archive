"""
Unit tests for storage architecture, environment variable overrides, and directory diagnostics (Phase 3).
"""

import os
from pathlib import Path
import pytest

from sih_archive.config import ArchiveConfig, get_config, reset_config


def test_default_config_paths():
    """Verify default paths resolve relative to repo root when environment is unset."""
    cfg = ArchiveConfig()
    assert cfg.archive_data_dir.name == "data"
    assert cfg.ground_truth_dir.name == "ground_truth"
    assert cfg.manifests_dir.name == "manifests"
    assert cfg.results_dir.name == "results"
    assert cfg.outputs_dir.name == "outputs"
    assert cfg.port == 8000
    assert cfg.host == "0.0.0.0"
    assert cfg.execution_mode == "DEMO"
    assert cfg.ocr_device == "cpu"


def test_env_var_path_overrides(monkeypatch, tmp_path):
    """Verify environment variables dynamically reconfigure storage mount paths."""
    custom_data = tmp_path / "custom_data"
    custom_gt = tmp_path / "custom_gt"
    custom_results = tmp_path / "custom_results"
    custom_cache = tmp_path / "custom_cache"

    monkeypatch.setenv("ARCHIVE_DATA_DIR", str(custom_data))
    monkeypatch.setenv("GROUND_TRUTH_DIR", str(custom_gt))
    monkeypatch.setenv("RESULTS_DIR", str(custom_results))
    monkeypatch.setenv("MODEL_CACHE_DIR", str(custom_cache))
    monkeypatch.setenv("PORT", "9090")
    monkeypatch.setenv("EXECUTION_MODE", "RESEARCH_VALIDATION")
    monkeypatch.setenv("OCR_DEVICE", "cuda")

    cfg = reset_config()
    assert cfg.archive_data_dir == custom_data.resolve()
    assert cfg.ground_truth_dir == custom_gt.resolve()
    assert cfg.results_dir == custom_results.resolve()
    assert cfg.model_cache_dir == custom_cache.resolve()
    assert cfg.port == 9090
    assert cfg.execution_mode == "RESEARCH_VALIDATION"
    assert cfg.ocr_device == "cuda"

    # Reset back to clean defaults
    monkeypatch.delenv("ARCHIVE_DATA_DIR", raising=False)
    monkeypatch.delenv("GROUND_TRUTH_DIR", raising=False)
    monkeypatch.delenv("RESULTS_DIR", raising=False)
    monkeypatch.delenv("MODEL_CACHE_DIR", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("EXECUTION_MODE", raising=False)
    monkeypatch.delenv("OCR_DEVICE", raising=False)
    reset_config()


def test_storage_status_and_writability(tmp_path):
    """Verify get_storage_status correctly detects directory existence and writability."""
    test_data = tmp_path / "data_vol"
    test_data.mkdir()

    cfg = ArchiveConfig(archive_data_dir=test_data)
    status = cfg.get_storage_status()

    assert "archive_data_dir" in status
    assert status["archive_data_dir"]["exists"] is True
    assert status["archive_data_dir"]["writable"] is True


def test_safe_diagnostics_omits_credentials():
    """Verify diagnostics dictionary does not leak sensitive information."""
    cfg = ArchiveConfig(database_url="postgresql://user:secretpass@db.northflank.app:5432/archive")
    diag = cfg.get_safe_diagnostics()

    assert "secretpass" not in str(diag)
    assert diag["has_database_url"] is True
    assert "storage_paths" in diag
    assert "execution_mode" in diag
