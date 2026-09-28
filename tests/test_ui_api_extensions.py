"""
Automated Integration and Unit Tests for UI Package Architecture and API Extensions.

Verifies:
- Page image serving (GET /api/v1/pages/{page_id}/image)
- Page metadata and regions (GET /api/v1/pages/{page_id})
- Cryptographic 6-stage provenance chain (GET /api/v1/provenance/{page_id})
- Historical timeline events (GET /api/v1/timeline)
- Audio-Visual media records with synced transcripts (GET /api/v1/media)
- Institutional admin & preservation audit (GET /api/v1/admin/audit)
- Enriched search hit fields in GET /api/v1/search
- Touchscreen kiosk route (GET /kiosk)
- UI package fixtures and builders directly
"""

import pytest
from fastapi.testclient import TestClient

from sih_archive.api.app import app
from sih_archive.ui.fixtures import (
    get_catalog_item,
    get_catalog_items,
    get_discovery_pathways,
    get_media_record,
    get_media_records,
    get_timeline_event,
    get_timeline_events,
)
from sih_archive.ui.page_builder import build_kiosk_html, build_portal_html
from sih_archive.ui.scripts import get_scripts
from sih_archive.ui.styles import THEME_TOKENS, get_styles


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with initialized lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Page Image Serving Tests
# -----------------------------------------------------------------------------

def test_page_image_endpoint_valid_page(client):
    """Verify GET /api/v1/pages/{page_id}/image returns 200 and image/png for existing scan."""
    res = client.get("/api/v1/pages/ambedkar_speech_vol1_p0001/image")
    assert res.status_code == 200
    assert "image/png" in res.headers["content-type"]
    assert len(res.content) > 1000  # Valid PNG binary bytes


def test_page_image_endpoint_with_png_extension(client):
    """Verify GET /api/v1/pages/{page_id}/image works when page_id includes .png suffix."""
    res = client.get("/api/v1/pages/ambedkar_speech_vol1_p0001.png/image")
    assert res.status_code == 200
    assert "image/png" in res.headers["content-type"]


def test_page_image_endpoint_missing_page(client):
    """Verify GET /api/v1/pages/{page_id}/image returns 404 and specific JSON error for missing scan."""
    res = client.get("/api/v1/pages/nonexistent_document_p9999/image")
    assert res.status_code == 404
    data = res.json()
    assert data["error"] == "Page image not found"


# -----------------------------------------------------------------------------
# 2. Page Metadata & Token Regions Tests
# -----------------------------------------------------------------------------

def test_page_metadata_endpoint_valid(client):
    """Verify GET /api/v1/pages/{page_id} returns structured metadata, bboxes, and ground-truth flags."""
    res = client.get("/api/v1/pages/ambedkar_speech_vol1_p0001")
    assert res.status_code == 200
    data = res.json()

    assert data["page_id"] == "ambedkar_speech_vol1_p0001"
    assert data["document_id"] == "ambedkar_speech_vol1"
    assert data["page_num"] == 1
    assert data["has_image"] is True
    assert data["ground_truth"] is True
    assert len(data["text"]) > 0
    assert len(data["regions"]) > 0

    first_region = data["regions"][0]
    assert "type" in first_region
    assert "text" in first_region
    assert "bbox" in first_region
    assert len(first_region["bbox"]) == 4
    assert all(isinstance(coord, int) for coord in first_region["bbox"])
    assert "confidence" in first_region
    assert 0.0 <= first_region["confidence"] <= 100.0


def test_page_metadata_endpoint_missing(client):
    """Verify GET /api/v1/pages/{page_id} returns 404 for completely unknown pages."""
    res = client.get("/api/v1/pages/unknown_doc_p9999")
    assert res.status_code == 404


# -----------------------------------------------------------------------------
# 3. 6-Stage Cryptographic Provenance Chain Tests
# -----------------------------------------------------------------------------

def test_provenance_endpoint_chain_structure(client):
    """Verify GET /api/v1/provenance/{page_id} returns all 6 stages with valid SHA-256 hashes."""
    res = client.get("/api/v1/provenance/ambedkar_speech_vol1_p0001")
    assert res.status_code == 200
    data = res.json()

    assert data["page_id"] == "ambedkar_speech_vol1_p0001"
    assert data["document_id"] == "ambedkar_speech_vol1"
    assert "stages" in data
    stages = data["stages"]
    assert len(stages) == 6

    expected_stages = [
        "source_object",
        "digital_copy",
        "page",
        "ocr_layout",
        "retrieval",
        "answer_derivative",
    ]

    for i, exp_stage in enumerate(expected_stages):
        stage = stages[i]
        assert stage["stage"] == exp_stage
        assert "name" in stage
        assert "status" in stage
        assert "sha256" in stage
        assert len(stage["sha256"]) == 64, f"Stage '{stage['stage']}' has invalid SHA-256 hash length"
        assert int(stage["sha256"], 16) >= 0  # Valid hex
        assert "details" in stage
        assert isinstance(stage["details"], dict)

    # Verify stage 1 has authentic manifest details
    src_details = stages[0]["details"]
    assert "title" in src_details
    assert "source_organization" in src_details
    assert src_details["rights_status"] == "public"


def test_provenance_endpoint_missing(client):
    """Verify GET /api/v1/provenance/{page_id} returns 404 for unknown records."""
    res = client.get("/api/v1/provenance/unknown_page_p9999")
    assert res.status_code == 404


# -----------------------------------------------------------------------------
# 4. Timeline Events Tests
# -----------------------------------------------------------------------------

def test_timeline_endpoint(client):
    """Verify GET /api/v1/timeline returns chronological milestones."""
    res = client.get("/api/v1/timeline")
    assert res.status_code == 200
    data = res.json()

    assert "total_events" in data
    assert data["total_events"] >= 10
    events = data["events"]
    assert len(events) == data["total_events"]

    event_ids = [e["id"] for e in events]
    assert "evt_1927_mahad_satyagraha" in event_ids
    assert "evt_1932_poona_pact" in event_ids
    assert "evt_1947_drafting_committee" in event_ids
    assert "evt_1949_constitution_adoption" in event_ids

    # Verify required keys in event objects
    first = events[0]
    for key in ("id", "year", "date", "title", "category", "description", "document_id", "page_id", "quote"):
        assert key in first, f"Missing key '{key}' in timeline event"


# -----------------------------------------------------------------------------
# 5. Audio-Visual Media Records Tests
# -----------------------------------------------------------------------------

def test_media_endpoint(client):
    """Verify GET /api/v1/media returns audio/video records with synchronized transcripts."""
    res = client.get("/api/v1/media")
    assert res.status_code == 200
    data = res.json()

    assert "total_items" in data
    assert data["total_items"] >= 3
    items = data["items"]
    assert len(items) == data["total_items"]

    types = {item["type"] for item in items}
    assert "audio" in types
    assert "video" in types

    first = items[0]
    for key in ("id", "title", "type", "duration", "speaker", "date", "language", "description", "transcript"):
        assert key in first, f"Missing key '{key}' in media item"

    assert len(first["transcript"]) > 0
    t_entry = first["transcript"][0]
    assert "start" in t_entry
    assert "speaker" in t_entry
    assert "text" in t_entry


# -----------------------------------------------------------------------------
# 6. Admin & Preservation Audit Tests
# -----------------------------------------------------------------------------

def test_admin_audit_endpoint(client):
    """Verify GET /api/v1/admin/audit returns storage health, manifest audit, and engine status."""
    res = client.get("/api/v1/admin/audit")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "operational"
    assert "timestamp" in data
    assert data["total_manifests"] >= 1
    assert "storage" in data
    assert "engines" in data
    assert "diagnostics" in data
    assert "intake_audit" in data

    intake = data["intake_audit"]
    assert intake["total_manifests"] == data["total_manifests"]
    assert "rights_breakdown" in intake
    assert "storage" in data and isinstance(data["storage"], dict)


# -----------------------------------------------------------------------------
# 7. Enriched Search Hit Serialization Tests
# -----------------------------------------------------------------------------

def test_enriched_search_hit_fields(client):
    """Verify GET /api/v1/search returns enriched hits with document_id, matched_regions, language, rights_status."""
    res = client.get("/api/v1/search?q=Ambedkar&engine=bm25&top_k=3")
    assert res.status_code == 200
    data = res.json()

    assert "hits" in data
    assert len(data["hits"]) > 0

    first_hit = data["hits"][0]
    # Invariant keys tested in test_api_server.py
    assert "page_id" in first_hit
    assert "score" in first_hit
    assert "text_snippet" in first_hit

    # Enriched keys
    assert "document_id" in first_hit
    assert first_hit["document_id"] == "ambedkar_speech_vol1"
    assert "matched_regions" in first_hit
    assert isinstance(first_hit["matched_regions"], list)
    assert "language" in first_hit
    assert first_hit["language"] in ("eng", "mar", "hin")
    assert "rights_status" in first_hit
    assert first_hit["rights_status"] == "public"


# -----------------------------------------------------------------------------
# 8. Kiosk UI Route Tests
# -----------------------------------------------------------------------------

def test_kiosk_route(client):
    """Verify GET /kiosk returns 200, HTML, DEMO banner, and touch UI shell."""
    res = client.get("/kiosk")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "DEMO & SYNTHETIC MODE" in res.text or "DEMO &amp; SYNTHETIC MODE" in res.text
    assert "Memorial Touch Kiosk" in res.text or "Touch" in res.text
    assert "Explore Manuscripts" in res.text
    assert "Chronological Timeline" in res.text


# -----------------------------------------------------------------------------
# 9. UI Package Fixtures and Builders Direct Unit Tests
# -----------------------------------------------------------------------------

def test_ui_package_fixtures_and_builders():
    """Verify all ui package exports function directly."""
    # Discovery pathways
    pathways = get_discovery_pathways()
    assert len(pathways) == 6
    pathway_ids = [p["id"] for p in pathways]
    assert "manuscripts_books" in pathway_ids
    assert "research_assistant" in pathway_ids

    # Catalog items
    catalog = get_catalog_items()
    assert len(catalog) >= 5
    item = get_catalog_item("ambedkar_speech_vol1")
    assert item is not None
    assert item["rights"] == "public"
    assert item["language"] == "eng"

    # Timeline events
    timeline = get_timeline_events()
    assert len(timeline) >= 10
    evt = get_timeline_event("evt_1927_mahad_satyagraha")
    assert evt is not None
    assert evt["year"] == 1927

    # Media records
    media = get_media_records()
    assert len(media) >= 3
    rec = get_media_record("media_ambedkar_bbc_1953")
    assert rec is not None
    assert len(rec["transcript"]) > 0

    # Styles and theme tokens
    assert "colors" in THEME_TOKENS
    assert "parchment" in THEME_TOKENS["colors"]
    styles = get_styles()
    assert "--primary" in styles

    # Scripts
    scripts = get_scripts()
    assert len(scripts) > 0

    # Page builders
    portal = build_portal_html()
    assert "DEMO & SYNTHETIC MODE" in portal
    assert "Resilient Document Retrieval" in portal

    kiosk = build_kiosk_html()
    assert "DEMO & SYNTHETIC MODE" in kiosk
    assert "Memorial Touch Kiosk" in kiosk
