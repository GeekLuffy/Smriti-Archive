"""
Tests for Vercel deployment entrypoint, serverless configuration, and platform constraints (SIH26096).
"""

import io
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.index import app as vercel_app
from sih_archive.config import ArchiveConfig, get_config, reset_config


@pytest.fixture(scope="module")
def vercel_client():
    """Provides a TestClient initialized against the Vercel entrypoint app."""
    with TestClient(vercel_app) as client:
        yield client


def test_vercel_entrypoint_imports_and_routes():
    """Verify that api/index.py exports a valid FastAPI instance with all required routes."""
    routes = [r.path for r in vercel_app.routes]
    assert "/health" in routes
    assert "/ready" in routes
    assert "/api/v1/diagnostics" in routes
    assert "/api/v1/search" in routes
    assert "/api/v1/qa" in routes
    assert "/api/v1/benchmarks/{phase}" in routes
    assert "/" in routes


def test_vercel_environment_configuration(monkeypatch):
    """Verify ArchiveConfig correctly adapts upload limits and platform mode under VERCEL=1."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("MAX_UPLOAD_SIZE_BYTES", raising=False)

    cfg = reset_config()
    assert cfg.is_vercel is True
    assert cfg.max_upload_size_bytes == 4 * 1024 * 1024  # 4MB ceiling for Vercel 4.5MB payload limit

    diag = cfg.get_safe_diagnostics()
    assert diag["is_vercel"] is True
    assert diag["platform_mode"] == "vercel_serverless"

    # Reset
    monkeypatch.delenv("VERCEL", raising=False)
    reset_config()


def test_readiness_in_serverless_readonly_mode(vercel_client, monkeypatch):
    """Verify /ready returns 200 in serverless mode when static directories exist even if read-only."""
    config = get_config()
    monkeypatch.setattr(config, "is_vercel", True)

    res = vercel_client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["is_serverless"] is True


def test_vercel_upload_size_informative_error(vercel_client, monkeypatch):
    """Verify that exceeding upload limit under Vercel explains the 4.5MB payload constraint."""
    config = get_config()
    monkeypatch.setattr(config, "is_vercel", True)
    monkeypatch.setattr(config, "max_upload_size_bytes", 50)  # Low limit for testing

    oversized = io.BytesIO(b"%PDF-1.4" + b"A" * 100)
    res = vercel_client.post(
        "/api/v1/ingest",
        data={
            "document_id": "test_oversized_vercel",
            "title": "Large Document",
            "source_organization": "Archive",
            "rights_status": "restricted",
            "rights_evidence": "Internal",
        },
        files={"file": ("large.pdf", oversized, "application/pdf")},
    )
    assert res.status_code == 413
    detail = res.json()["detail"]
    assert "Vercel serverless functions enforce a 4.5MB payload limit" in detail
    assert "direct-to-object-storage" in detail


def test_vercel_diagnostics_truthful_ocr(vercel_client):
    """Verify /api/v1/diagnostics reports OCR host engine status gracefully without fabricating metrics."""
    res = vercel_client.get("/api/v1/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert "ocr_host_engine" in data
    assert "available" in data["ocr_host_engine"]
    assert "diagnostic_message" in data["ocr_host_engine"]
    assert "research_integrity_notice" in data
    assert "NOT ESTABLISHED BY SOFTWARE TEST" in data["research_integrity_notice"]


def test_vercel_demo_mode_active_by_default(vercel_client):
    """Verify demo mode disclaimer is served on root HTML page and search responses."""
    # Check HTML demo UI
    res_ui = vercel_client.get("/")
    assert res_ui.status_code == 200
    assert "DEMO" in res_ui.text
    assert "SYNTHETIC" in res_ui.text

    # Check Search response
    res_search = vercel_client.get("/api/v1/search?q=Ambedkar&engine=hybrid")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert "DEMO" in search_data["execution_mode"]
    assert "NOT VALIDATED EMPIRICAL HISTORICAL RESULTS" in search_data["disclaimer"]
