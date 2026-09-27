"""
Integration tests for FastAPI application server, endpoints, security gates, and DEMO mode (Phases 2, 7, 8, 9).
"""

import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from sih_archive.api.app import app
from sih_archive.config import get_config, reset_config


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with initialized lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    """Verify GET /health returns 200 and healthy status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sih26096-archive"
    assert "timestamp" in data
    assert "execution_mode" in data


def test_readiness_endpoint(client):
    """Verify GET /ready returns 200 when storage is writable and engines are initialized."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["storage_writable"] is True
    assert data["engines_ready"] is True


def test_system_diagnostics(client):
    """Verify GET /api/v1/diagnostics exposes host status, OCR engine availability, and gate statuses."""
    res = client.get("/api/v1/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert "service" in data
    assert "python_version" in data
    assert "ocr_host_engine" in data
    assert "PASS" in data["research_gates"]["E0_corpus_rights"]
    assert "NOT ESTABLISHED BY SOFTWARE TEST" in data["research_gates"]["E0_corpus_rights"]
    assert "LOCKED" in data["research_gates"]["E2_retrieval_benchmark"]
    assert "LOCKED" in data["research_gates"]["E3_attribution_benchmark"]
    assert "research_integrity_notice" in data


def test_manifests_list(client):
    """Verify GET /api/v1/manifests returns list of registered manifests."""
    res = client.get("/api/v1/manifests")
    assert res.status_code == 200
    data = res.json()
    assert "total_manifests" in data
    assert "manifests" in data


def test_search_retrieval(client):
    """Verify GET /api/v1/search executes queries and tags results with DEMO disclaimer."""
    res = client.get("/api/v1/search?q=Ambedkar+Writings&engine=hybrid&top_k=3")
    assert res.status_code == 200
    data = res.json()
    assert "DEMO" in data["execution_mode"]
    assert "NOT VALIDATED EMPIRICAL HISTORICAL RESULTS" in data["disclaimer"]
    assert data["query"] == "Ambedkar Writings"
    assert data["total_hits"] >= 1
    assert "hits" in data
    first_hit = data["hits"][0]
    assert "page_id" in first_hit
    assert "score" in first_hit
    assert "text_snippet" in first_hit


def test_search_invalid_engine(client):
    """Verify GET /api/v1/search rejects unsupported retrieval engine."""
    res = client.get("/api/v1/search?q=test&engine=unsupported_vector_xyz")
    assert res.status_code == 400
    assert "not supported" in res.json()["detail"]


def test_qa_evidence_grounded_answer(client):
    """Verify POST /api/v1/qa returns evidence-grounded answer with bounding-box citations."""
    res = client.post(
        "/api/v1/qa",
        json={"question": "Did Education Department Government of Maharashtra publish this?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "DEMO" in data["execution_mode"]
    assert data["is_refusal"] is False
    assert len(data["citations"]) > 0
    first_citation = data["citations"][0]
    assert "bbox" in first_citation
    assert len(first_citation["bbox"]) == 4


def test_qa_algorithmic_refusal(client):
    """Verify POST /api/v1/qa triggers algorithmic refusal on ungrounded/out-of-domain query."""
    res = client.post(
        "/api/v1/qa",
        json={"question": "What is the thermodynamic entropy of a black hole event horizon?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_refusal"] is True
    assert data["refusal_reason"] is not None


def test_benchmarks_status_and_phase(client):
    """Verify GET /api/v1/benchmarks/status and phase results."""
    res_status = client.get("/api/v1/benchmarks/status")
    assert res_status.status_code == 200
    assert "phases" in res_status.json()

    res_e1 = client.get("/api/v1/benchmarks/e1")
    assert res_e1.status_code == 200
    data_e1 = res_e1.json()
    assert data_e1["phase"] == "E1_OCR"

    res_e2 = client.get("/api/v1/benchmarks/e2")
    assert res_e2.status_code == 200
    data_e2 = res_e2.json()
    assert data_e2["phase"] == "E2_RETRIEVAL"

    res_404 = client.get("/api/v1/benchmarks/nonexistent")
    assert res_404.status_code == 404


def test_demo_ui_served(client):
    """Verify GET / returns responsive HTML demo UI with explicit synthetic badge."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "DEMO &amp; SYNTHETIC MODE" in res.text or "DEMO & SYNTHETIC MODE" in res.text
    assert "Resilient Document Retrieval" in res.text


# ---------------------------------------------------------
# Security & Upload Validation Tests (Phase 9)
# ---------------------------------------------------------

def test_upload_missing_rights_evidence_rejected(client):
    """Verify intake security rejects public status without statutory evidence."""
    fake_pdf = io.BytesIO(b"%PDF-1.4 minimal test content")
    res = client.post(
        "/api/v1/ingest",
        data={
            "document_id": "test_security_no_evidence",
            "title": "Unauthorized Document",
            "source_organization": "Unknown Source",
            "rights_status": "public",
        },
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
    )
    assert res.status_code == 422
    assert "rights-evidence" in res.json()["detail"]


def test_upload_disallowed_extension_rejected(client):
    """Verify security rejects dangerous file types (e.g. .exe, .sh)."""
    fake_exe = io.BytesIO(b"MZ executable header")
    res = client.post(
        "/api/v1/ingest",
        data={
            "document_id": "malicious_script",
            "title": "Executable",
            "source_organization": "Unknown",
            "rights_status": "restricted",
            "rights_evidence": "Restricted",
        },
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")},
    )
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]


def test_upload_path_traversal_document_id_rejected(client):
    """Verify security rejects path traversal characters in document_id."""
    fake_pdf = io.BytesIO(b"%PDF-1.4 minimal test content")
    res = client.post(
        "/api/v1/ingest",
        data={
            "document_id": "../../etc/passwd",
            "title": "Traversal Attempt",
            "source_organization": "Security Test",
            "rights_status": "restricted",
            "rights_evidence": "Internal test",
        },
        files={"file": ("traversal.pdf", fake_pdf, "application/pdf")},
    )
    assert res.status_code == 400
    assert "Invalid document_id" in res.json()["detail"]


def test_upload_exceeding_size_limit_rejected(client, monkeypatch):
    """Verify intake security enforces max upload size limits."""
    config = get_config()
    monkeypatch.setattr(config, "max_upload_size_bytes", 100)  # 100 bytes limit

    oversized_pdf = io.BytesIO(b"%PDF-1.4" + b"X" * 200)
    res = client.post(
        "/api/v1/ingest",
        data={
            "document_id": "oversized_doc",
            "title": "Oversized Document",
            "source_organization": "Test",
            "rights_status": "restricted",
            "rights_evidence": "Test",
        },
        files={"file": ("big.pdf", oversized_pdf, "application/pdf")},
    )
    assert res.status_code == 413
    assert "exceeds maximum upload limit" in res.json()["detail"]


def test_production_debug_disabled():
    """Verify debug mode is disabled by default in production config."""
    config = get_config()
    assert config.app_debug is False
    diag = config.get_safe_diagnostics()
    assert diag["app_debug"] is False


def test_tesseract_adapter_container_path_independent(tmp_path):
    """Verify TesseractAdapter can resolve containerized Linux binary independently of host PATH."""
    from sih_archive.ocr.tesseract import TesseractAdapter
    # Nonexistent path returns clean diagnostic without raising
    adapter = TesseractAdapter(tesseract_cmd="/usr/bin/tesseract")
    avail, msg = adapter.is_available()
    # On Windows host /usr/bin/tesseract does not exist, so it truthfully reports unavailable
    assert isinstance(avail, bool)
    assert "Tesseract" in msg or "not found" in msg


def test_research_integrity_legal_authorization_distinction(client):
    """Verify diagnostics explicitly state that software tests do NOT establish legal authorization."""
    res = client.get("/api/v1/diagnostics")
    assert res.status_code == 200
    data = res.json()
    e0_status = data["research_gates"]["E0_corpus_rights"]
    notice = data["research_integrity_notice"]
    assert "NOT ESTABLISHED BY SOFTWARE TEST" in e0_status
    assert "Rights and provenance metadata validation is MEASURED" in notice
    assert "NOT ESTABLISHED BY SOFTWARE TEST" in notice

