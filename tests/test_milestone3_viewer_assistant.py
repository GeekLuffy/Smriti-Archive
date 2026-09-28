"""
Automated Verification Suite for Milestone 3: Archival Manuscript Viewer, AI Research Assistant & Provenance/Timeline.

Verifies:
- Requirement R4: Archival Document & Manuscript Viewer with 3-column layout, pan/zoom toolbar,
  canvas with 300 DPI image, bounding-box overlay with 'SOURCE EVIDENCE' badge, truthful degradation
  notice ('Region-level evidence unavailable for this record.'), and 6-stage provenance button.
- Requirement R5: Institutional AI Research Assistant with structured 3-column layout (session history,
  structured research question input, persistent evidence drawer / citation inspector with numbered citations,
  minimal enclosing bbox, attribution score, claim text), and principled algorithmic refusal card
  ('Insufficient archival evidence found for a supported answer.').
- Requirement R6: Provenance continuity interactive 6-stage chain (SOURCE OBJECT -> DIGITAL COPY -> PAGE ->
  OCR/LAYOUT -> RETRIEVAL -> ANSWER/DERIVATIVE) with cryptographic SHA-256 hashes, statutory rights evidence,
  and chronological heritage timeline (1916-1956) with 4 era filters and direct inspection buttons.
- Preservation of all invariants, backward compatibility, and 100% test passing.
"""

import pytest
from fastapi.testclient import TestClient

from sih_archive.api.app import app
from sih_archive.ui.fixtures import (
    get_catalog_items,
    get_timeline_events,
    get_viewer_pages,
)
from sih_archive.ui.page_builder import build_portal_html
from sih_archive.ui.scripts import get_scripts
from sih_archive.ui.styles import THEME_TOKENS, get_styles


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with initialized lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Requirement R4: Archival Document & Manuscript Viewer Tests
# -----------------------------------------------------------------------------

def test_viewer_three_column_layout_and_pan_zoom_controls(client):
    """Verify Viewer 3-column layout structure and pan/zoom toolbar controls."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 3-column Layout structure
    assert 'class="viewer-layout"' in html
    assert 'class="viewer-left-col"' in html
    assert 'class="viewer-center-col"' in html
    assert 'class="viewer-right-col"' in html

    # Left Column: Thumbnail strip and selectable folios
    assert 'class="thumbnail-strip"' in html
    assert 'thumb-ambedkar_speech_vol1_p0001' in html
    assert 'thumb-ambedkar_speech_vol1_p0002' in html
    assert 'thumb-ambedkar_speech_vol1_p0003' in html
    assert 'thumb-ambedkar_speech_vol1_p0004' in html
    assert 'thumb-ambedkar_speech_vol1_p0005' in html
    assert "/api/v1/pages/ambedkar_speech_vol1_p0001/image" in html
    assert "300 DPI" in html

    # Center Column: Pan/Zoom toolbar
    assert 'class="viewer-toolbar"' in html
    assert 'id="btn-zoom-in"' in html
    assert "Zoom In" in html
    assert 'id="btn-zoom-out"' in html
    assert "Zoom Out" in html
    assert 'id="btn-zoom-reset"' in html
    assert "Reset 100%" in html
    assert 'id="btn-fit-width"' in html
    assert "Fit Width" in html
    assert 'id="btn-pan-toggle"' in html
    assert "Pan Mode" in html
    assert 'id="zoom-level-indicator"' in html

    # Center Column: Canvas and image container
    assert 'id="viewer-canvas-container"' in html
    assert 'id="viewer-transform-wrap"' in html
    assert 'id="viewer-image"' in html
    assert 'id="viewer-bbox-overlay"' in html

    # Right Column: Metadata, transcript inspection, token regions & provenance button
    assert 'id="viewer-metadata-box"' in html
    assert 'id="viewer-transcript-text"' in html
    assert 'id="viewer-token-regions-list"' in html
    assert "Inspect Chain of Custody (6-Stage Provenance) 🔗" in html


def test_viewer_source_evidence_badge_and_truthful_degradation(client):
    """Verify SOURCE EVIDENCE tag and truthful degradation message when coordinates unavailable."""
    res = client.get("/")
    html = res.text
    scripts = get_scripts()

    # SOURCE EVIDENCE badge
    assert "SOURCE EVIDENCE" in scripts

    # Truthful Degradation: required exact notice
    assert "Region-level evidence unavailable for this record." in html
    assert "Region-level evidence unavailable for this record." in scripts

    # Verify live page metadata endpoint returns real token coordinates for valid page
    res_page = client.get("/api/v1/pages/ambedkar_speech_vol1_p0001")
    assert res_page.status_code == 200
    pdata = res_page.json()
    assert pdata["page_id"] == "ambedkar_speech_vol1_p0001"
    assert len(pdata["regions"]) > 0
    first_reg = pdata["regions"][0]
    assert "bbox" in first_reg
    assert len(first_reg["bbox"]) == 4
    assert first_reg["confidence"] > 0

    # Verify missing page returns 404 cleanly
    res_missing = client.get("/api/v1/pages/non_existent_page_p9999")
    assert res_missing.status_code == 404


def test_viewer_pan_zoom_script_functions():
    """Verify JavaScript provides pan/zoom engine functions."""
    scripts = get_scripts()
    assert "function zoomIn(" in scripts
    assert "function zoomOut(" in scripts
    assert "function resetZoom(" in scripts
    assert "function fitWidth(" in scripts
    assert "function togglePanMode(" in scripts
    assert "function updateViewerTransform(" in scripts
    assert "function renderSingleBBox(" in scripts


def test_viewer_pages_fixtures_data():
    """Verify get_viewer_pages() provides 5 structured folios."""
    pages = get_viewer_pages()
    assert len(pages) == 5
    page_ids = [p["page_id"] for p in pages]
    assert "ambedkar_speech_vol1_p0001" in page_ids
    assert "ambedkar_speech_vol1_p0005" in page_ids
    for p in pages:
        assert p["dpi"] == 300
        assert p["rights"] == "public"
        assert "title" in p
        assert p["ocr_confidence"] >= 90.0


# -----------------------------------------------------------------------------
# 2. Requirement R5: Institutional AI Research Assistant Tests
# -----------------------------------------------------------------------------

def test_research_assistant_structured_layout(client):
    """Verify Assistant 3-column layout (session history, question stream, evidence drawer)."""
    res = client.get("/")
    html = res.text

    # 3-column Layout
    assert 'class="assistant-layout"' in html
    assert 'class="assistant-left-col"' in html
    assert 'class="assistant-center-col"' in html
    assert 'class="assistant-right-col"' in html

    # Left Column: Session history & citation topics
    assert 'class="session-history-pane"' in html
    assert 'id="assistant-session-history"' in html
    assert 'id="assistant-citation-tags"' in html
    assert "#WritingsAndSpeeches" in html
    assert "#Constitution1950" in html

    # Center Column: Research question input & answer stream
    assert 'id="qa-input-assistant"' in html
    assert 'id="btn-submit-assistant-qa"' in html
    assert 'id="assistant-answer-stream"' in html
    assert "Structured Archival Inquiry" in html
    assert "Suggested queries:" in html

    # Right Column: Persistent Evidence Drawer / Citation Inspector
    assert 'class="evidence-drawer-pane"' in html
    assert "Persistent Evidence Drawer" in html
    assert "Citation Inspector" in html
    assert "Attribution Verification" in html
    assert 'id="assistant-citations-list"' in html


def test_research_assistant_live_supported_qa_and_citations(client):
    """Verify live POST /api/v1/qa produces factual answer and numbered citations with bbox."""
    res = client.post(
        "/api/v1/qa",
        json={"question": "Did Education Department Government of Maharashtra publish this?"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["is_refusal"] is False
    assert len(data["citations"]) > 0
    assert "DEMO" in data["execution_mode"]

    citation = data["citations"][0]
    assert citation["document_id"] == "ambedkar_speech_vol1"
    assert citation["page_id"] == "ambedkar_speech_vol1_p0001"
    assert len(citation["bbox"]) == 4
    assert citation["confidence"] > 0
    assert len(citation["quote_span"]) > 0


def test_research_assistant_principled_algorithmic_refusal(client):
    """Verify live POST /api/v1/qa triggers principled algorithmic refusal on ungrounded query."""
    res = client.post(
        "/api/v1/qa",
        json={"question": "What is the thermodynamic entropy of a black hole event horizon?"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["is_refusal"] is True
    assert data["refusal_reason"] is not None

    # Check client script and page builder render the exact refusal card text
    scripts = get_scripts()
    assert "Insufficient archival evidence found for a supported answer." in scripts

    portal_html = build_portal_html()
    assert "Insufficient archival evidence found for a supported answer." in portal_html


def test_research_assistant_scripts_interaction_contract():
    """Verify get_scripts() provides executeAssistantQA, session history, and citation drawer logic."""
    scripts = get_scripts()
    assert "function executeAssistantQA(" in scripts
    assert "function renderSessionHistory(" in scripts
    assert "function selectSuggestedQuery(" in scripts
    assert "Citation [" in scripts
    assert "Source Document" in scripts
    assert "Page Number" in scripts
    assert "View Source →" in scripts


# -----------------------------------------------------------------------------
# 3. Requirement R6: Provenance Continuity & Heritage Timeline Tests
# -----------------------------------------------------------------------------

def test_provenance_modal_and_six_stage_chain(client):
    """Verify Provenance modal displays the 6-stage chain with SHA-256 hashes."""
    res = client.get("/")
    html = res.text

    assert 'id="provenance-modal"' in html
    assert 'id="provenance-chain-content"' in html
    assert "SOURCE OBJECT → DIGITAL COPY → PAGE → OCR/LAYOUT → RETRIEVAL → ANSWER/DERIVATIVE" in html

    scripts = get_scripts()
    assert "function showProvenance(" in scripts
    assert "function closeProvenance(" in scripts
    assert "SOURCE OBJECT" in scripts
    assert "DIGITAL COPY" in scripts
    assert "PAGE" in scripts
    assert "OCR/LAYOUT" in scripts
    assert "RETRIEVAL" in scripts
    assert "ANSWER/DERIVATIVE" in scripts

    # Verify live API provenance endpoint returns all 6 stages
    res_prov = client.get("/api/v1/provenance/ambedkar_speech_vol1_p0001")
    assert res_prov.status_code == 200
    data = res_prov.json()
    assert len(data["stages"]) == 6

    stage_names = [s["name"] for s in data["stages"]]
    assert "Source Object" in stage_names
    assert "Digital Copy" in stage_names
    assert "Page Rendering" in stage_names
    assert "OCR & Layout Analysis" in stage_names
    assert "Retrieval Indexing" in stage_names
    assert "Answer & Citation Grounding" in stage_names

    for stage in data["stages"]:
        assert len(stage["sha256"]) == 64
        assert stage["status"] in ("VERIFIED", "RENDERED", "PROCESSED", "INDEXED", "VERIFIED_GROUNDING")


def test_heritage_timeline_rendering_and_era_filters(client):
    """Verify chronological timeline rendering (1916-1956) with 4 era filters."""
    res = client.get("/")
    html = res.text

    # Section title
    assert "Chronological Heritage Milestones (1916–1956)" in html or "Chronological Heritage Milestones (1916-1956)" in html

    # Era filter bar and pills
    assert 'class="timeline-era-bar"' in html
    assert 'data-era="all"' in html
    assert 'data-era="early_academic"' in html
    assert 'data-era="social_movements"' in html
    assert 'data-era="drafting_constitution"' in html
    assert 'data-era="post_independence"' in html

    # Direct document inspect button on each timeline card
    assert "Inspect Archival Document →" in html

    # Verify live timeline API endpoint
    res_tl = client.get("/api/v1/timeline")
    assert res_tl.status_code == 200
    tdata = res_tl.json()
    assert tdata["total_events"] == 16
    assert len(tdata["events"]) == 16

    # Verify era distribution
    events = tdata["events"]
    early = [e for e in events if 1916 <= e["year"] <= 1926]
    social = [e for e in events if 1927 <= e["year"] <= 1945]
    drafting = [e for e in events if 1946 <= e["year"] <= 1950]
    post = [e for e in events if 1951 <= e["year"] <= 1956]

    assert len(early) >= 3
    assert len(social) >= 5
    assert len(drafting) >= 5
    assert len(post) >= 1

    # Check client script filterTimeline function
    scripts = get_scripts()
    assert "function filterTimeline(" in scripts


# -----------------------------------------------------------------------------
# 4. Critical Invariants & Zero-Regression Guardrail Tests
# -----------------------------------------------------------------------------

def test_critical_invariants_preserved(client):
    """Verify all critical invariant strings remain present on GET /."""
    res = client.get("/")
    assert res.status_code == 200
    text = res.text

    assert "DEMO & SYNTHETIC MODE" in text or "DEMO &amp; SYNTHETIC MODE" in text
    assert "Resilient Document Retrieval" in text
    assert "/kiosk" in text
    assert "TEAM ORBIT — National Digital Heritage Infrastructure" in text
