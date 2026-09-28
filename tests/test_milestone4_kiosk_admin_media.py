"""
Tests for Milestone 4: Multilingual Access, A/V Media Library, Institutional Admin Workspace,
and Touchscreen Kiosk & Smart Display Mode (SIH26096 Requirements R7, R8, R9).
"""

from fastapi.testclient import TestClient
import pytest

from sih_archive.api.app import app
from sih_archive.ui.fixtures import (
    MEDIA_RECORDS,
    VIEWER_PAGES,
    get_media_record,
    get_media_records,
    get_viewer_page,
    get_viewer_pages,
)
from sih_archive.ui.page_builder import build_kiosk_html, build_portal_html
from sih_archive.ui.styles import get_styles


@pytest.fixture
def client():
    return TestClient(app)


# =============================================================================
# 1. R7: MULTILINGUAL ACCESS TESTS
# =============================================================================

def test_multilingual_viewer_pages_fixtures():
    """Verify viewer page fixtures contain original language, original text, and multilingual translations."""
    pages = get_viewer_pages()
    assert len(pages) >= 5

    # Check Folio 1 (English original with Hindi & Marathi translations)
    p1 = get_viewer_page("ambedkar_speech_vol1_p0001")
    assert p1 is not None
    assert p1["original_lang"] == "en"
    assert "Title Page" in p1["title"]
    assert "Writings and Speeches" in p1["subtitle"]
    assert "DR. BABASAHEB AMBEDKAR" in p1["original_text"]
    assert "hi" in p1["translations"]
    assert "mr" in p1["translations"]
    assert "बाबासाहेब" in p1["translations"]["hi"]
    assert "भाषणे" in p1["translations"]["mr"]

    # Check Folio 3 (Marathi original Mahad Declaration with English & Hindi translations)
    p3 = get_viewer_page("ambedkar_speech_vol1_p0003")
    assert p3 is not None
    assert p3["original_lang"] == "mr"
    assert "चवदार तळ्याचे पाणी" in p3["original_text"]
    assert "en" in p3["translations"]
    assert "hi" in p3["translations"]
    assert "Chavdar Tank" in p3["translations"]["en"]
    assert "चवदार तालाब" in p3["translations"]["hi"]


def test_multilingual_portal_html_elements(client):
    """Verify portal HTML contains multilingual toggle controls, language tags, and persistent fallback."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Multilingual bar and toggles
    assert "multilingual-bar" in html
    assert "btn-lang-original" in html
    assert "btn-lang-translated" in html
    assert "Original Source" in html
    assert "Translated Layer" in html

    # Language metadata tags
    assert "viewer-active-lang-tag" in html
    assert "lang-metadata-tag" in html

    # Persistent fallback link
    assert "view-original-fallback" in html
    assert "View original source" in html

    # CSS classes for side-by-side or translated layer
    styles = get_styles()
    assert ".translation-side-by-side" in styles
    assert ".translation-col" in styles
    assert ".lang-btn" in styles
    assert ".view-original-fallback" in styles


# =============================================================================
# 2. R7: AUDIO-VISUAL MEDIA LIBRARY TESTS
# =============================================================================

def test_media_records_fixtures_and_resolver():
    """Verify media records fixtures with aliases, duration, and time-coded synchronized transcripts."""
    records = get_media_records()
    assert len(records) >= 3

    # Verify resolution by primary ID and alias
    bbc_rec = get_media_record("bbc_interview_1953")
    assert bbc_rec is not None
    assert "BBC Radio Interview" in bbc_rec["title"]
    assert bbc_rec["duration_seconds"] == 225
    assert len(bbc_rec["transcript"]) >= 4

    # Verify Cad speech
    cad_rec = get_media_record("constituent_assembly_speech_1949")
    assert cad_rec is not None
    assert "Constituent Assembly" in cad_rec["title"]
    assert cad_rec["type"] == "video"

    # Verify Mahad address
    mahad_rec = get_media_record("mahad_memorial_address_1927")
    assert mahad_rec is not None
    assert "Satyagraha" in mahad_rec["title"]
    assert mahad_rec["language"] == "mar"

    # Check transcript timecode structure and second offsets
    for line in bbc_rec["transcript"]:
        assert "speaker" in line
        assert "start" in line
        assert "text" in line
        assert "seconds" in line
        assert line["seconds"] >= 0


def test_media_api_endpoint(client):
    """Verify GET /api/v1/media endpoint returns all archival media records."""
    res = client.get("/api/v1/media")
    assert res.status_code == 200
    data = res.json()
    assert "total_items" in data or "total" in data
    total_val = data.get("total_items") or data.get("total")
    assert total_val >= 3
    assert "items" in data
    ids = [item["id"] for item in data["items"]]
    assert any("bbc" in i for i in ids)
    assert any("cad" in i for i in ids)


def test_media_player_ui_elements(client):
    """Verify portal HTML contains media player controls, scrubber, time display, and synced transcript."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Media selector and player container
    assert "media-selector-bar" in html
    assert "media-player-container" in html
    assert "media-screen" in html
    assert "waveform-bars" in html

    # Controls: play/pause, scrubber, time display, volume
    assert "media-play-pause-btn" in html
    assert "media-scrubber" in html
    assert "media-time-display" in html
    assert "media-volume-btn" in html

    # Synchronized transcript pane and timecodes
    assert "synced-transcript-pane" in html
    assert "media-transcript-lines" in html
    assert "transcript-line" in html
    assert "[00:00]" in html
    assert "[00:32]" in html

    # Speaker notes, historical context, and related catalog records
    assert "media-speaker-notes" in html
    assert "media-historical-context" in html
    assert "media-related-records" in html


# =============================================================================
# 3. R7: INSTITUTIONAL ADMIN WORKSPACE TESTS
# =============================================================================

def test_admin_audit_and_diagnostics_endpoints(client):
    """Verify live institutional audit and diagnostics endpoints serve valid data."""
    audit_res = client.get("/api/v1/admin/audit")
    assert audit_res.status_code == 200
    audit = audit_res.json()
    assert audit["status"] == "operational"
    assert "manifests" in audit
    assert len(audit["manifests"]) >= 1
    assert "storage" in audit
    assert "engines" in audit

    diag_res = client.get("/api/v1/diagnostics")
    assert diag_res.status_code == 200
    diag = diag_res.json()
    assert "python_version" in diag
    assert "ocr_host_engine" in diag
    assert "research_integrity_notice" in diag


def test_admin_workspace_ui_sections_and_badges(client):
    """Verify institutional admin dashboard contains the 5 required audit areas and all 4 status badges."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Admin workspace container
    assert "admin-workspace-content" in html
    assert "Institutional Administration & Audit Workspace" in html

    # 5 required audit areas:
    # 1. Ingestion queues & document manifests
    assert "1. Ingestion Queues & Document Manifests" in html
    # 2. OCR pipeline status & engine availability
    assert "2. OCR Pipeline Status & Engine Availability" in html
    # 3. Rights & IP compliance audits
    assert "3. Rights & IP Compliance Audits" in html
    # 4. Preservation storage & SHA-256 integrity checksums
    assert "4. Preservation Storage & SHA-256 Integrity" in html
    assert "SHA-256" in html
    # 5. System health and diagnostic metrics
    assert "5. System Health, Diagnostics & Operational Metrics" in html

    # Status badges
    assert "badge-status-verified" in html
    assert "VERIFIED" in html
    assert "badge-status-processing" in html
    assert "PROCESSING" in html
    assert "badge-status-review" in html
    assert "REVIEW REQUIRED" in html
    assert "badge-status-unknown" in html
    assert "UNKNOWN" in html


# =============================================================================
# 4. R8: DEDICATED TOUCHSCREEN KIOSK & SMART DISPLAY MODE TESTS
# =============================================================================

def test_kiosk_touch_navigation_and_targets():
    """Verify Kiosk HTML has simplified touch buttons and enforces >= 48px touch targets."""
    kiosk_html = build_kiosk_html()

    # Touch target minimum requirement
    assert "--kiosk-touch-min: 48px;" in kiosk_html
    assert "min-height: 48px;" in kiosk_html
    assert "min-width: 48px;" in kiosk_html

    # Simplified 6 touch navigation buttons
    assert "Explore Heritage" in kiosk_html
    assert "Search" in kiosk_html
    assert "Timeline" in kiosk_html
    assert "Listen" in kiosk_html
    assert "Watch" in kiosk_html
    assert "Ask" in kiosk_html

    # Backwards-compatible labels for existing test assertions
    assert "Explore Manuscripts" in kiosk_html
    assert "Chronological Timeline" in kiosk_html

    # Touch search & topic cards
    assert "kiosk-search-input" in kiosk_html
    assert "kiosk-search-btn" in kiosk_html
    assert "topic-chip" in kiosk_html
    assert "Constitution" in kiosk_html
    assert "Mahad Satyagraha" in kiosk_html


def test_smart_display_ambient_mode_in_kiosk():
    """Verify Smart Display Mode ambient slideshow, progress bar, and pause/resume logic."""
    kiosk_html = build_kiosk_html()

    # Smart display overlay & toggle
    assert "ambient-display-mode" in kiosk_html
    assert "btn-ambient-toggle" in kiosk_html
    assert "Smart Display Mode" in kiosk_html

    # Progress bar and cycling timing
    assert "ambient-progress-bar" in kiosk_html
    assert "DURATION_MS = 8000" in kiosk_html  # 8-second cycling

    # Pause/Resume functionality
    assert "onAmbientTouch" in kiosk_html
    assert "PAUSED (Touch to Resume)" in kiosk_html
    assert "Space" in kiosk_html

    # Curated archival exhibits
    assert "Castes in India" in kiosk_html
    assert "Annihilation of Caste" in kiosk_html
    assert "Constituent Assembly Final Address" in kiosk_html


def test_kiosk_routes_and_mode_parameters(client):
    """Verify GET /kiosk, GET /?mode=kiosk, and GET /kiosk?mode=ambient."""
    # Dedicated /kiosk route
    res_kiosk = client.get("/kiosk")
    assert res_kiosk.status_code == 200
    assert "text/html" in res_kiosk.headers["content-type"]
    assert "Memorial Touch Kiosk" in res_kiosk.text
    assert "Explore Heritage" in res_kiosk.text

    # Mode = kiosk on root URL
    res_root_kiosk = client.get("/?mode=kiosk")
    assert res_root_kiosk.status_code == 200
    assert "Memorial Touch Kiosk" in res_root_kiosk.text

    # Mode = ambient on root URL
    res_root_ambient = client.get("/?mode=ambient")
    assert res_root_ambient.status_code == 200
    assert "ambient-display-mode" in res_root_ambient.text
    assert "true || params.get(\"mode\") === \"ambient\"" in res_root_ambient.text

    # Mode = ambient on /kiosk route
    res_kiosk_ambient = client.get("/kiosk?mode=ambient")
    assert res_kiosk_ambient.status_code == 200
    assert "ambient-display-mode" in res_kiosk_ambient.text


# =============================================================================
# 5. R9: RESEARCH INTEGRITY GUARDRAILS & INVARIANTS
# =============================================================================

def test_research_integrity_demo_disclaimers(client):
    """Verify prominent DEMO Banner and invariant strings across both Portal and Kiosk views."""
    # Root portal view
    res_portal = client.get("/")
    assert res_portal.status_code == 200
    assert "DEMO & SYNTHETIC MODE" in res_portal.text or "DEMO &amp; SYNTHETIC MODE" in res_portal.text
    assert "Resilient Document Retrieval" in res_portal.text
    assert "NOT VALIDATED EMPIRICAL HISTORICAL RESULTS" in res_portal.text

    # Kiosk view
    res_kiosk = client.get("/kiosk")
    assert res_kiosk.status_code == 200
    assert "DEMO & SYNTHETIC MODE" in res_kiosk.text or "DEMO &amp; SYNTHETIC MODE" in res_kiosk.text
    assert "Resilient Document Retrieval" in res_kiosk.text
    assert "NOT VALIDATED EMPIRICAL HISTORICAL RESULTS" in res_kiosk.text
