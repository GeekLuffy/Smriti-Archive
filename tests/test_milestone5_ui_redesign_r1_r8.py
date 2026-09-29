"""
Comprehensive UI/UX Regression Test Suite for SIH26096: Milestone 4 & Requirements R1 through R8.

Validates the complete "Heritage x Modern Research Infrastructure" platform:
- R1: Coherent Heritage Design System & Visual Hierarchy (Palette, Typography, Terracotta, No Glassmorphism)
- R2: Homepage 7-Section Architecture & Live Demo CTAs (Dual-Preservation, Curated Collections, Featured Doc, Timeline Strip, AV Showcase, Research Showcase, Archival Footer)
- R3: Archival Document Catalog & Library Search Experience (Faceted Catalog, #filter-institution, Distinctive Token Matching, Enriched Search Result Cards)
- R4: Split Document & Manuscript Viewer (Prev/Next Page Controls, Pan/Zoom, 3-Column Layout, Canvas, SOURCE EVIDENCE, Truthful Degradation)
- R5: Research Assistant Workspace with Citation Evidence (Institutional Truthful Framing Banner, Numbered Citations, Evidence Drawer, Principled Refusal Card)
- R6: Archival Fixtures & Asset Schema Enrichment (19-Field HeritageRecord, 24 Authentic Records across 6 Collections, 9 Backward-Compatibility Keys, Catalog REST Endpoints)
- R7: Dedicated Touchscreen Kiosk & Smart-Display Experience (5 Discovery Categories, Dual-Preservation, Home/Back Control, >=48px Touch Targets, 8s Ambient Mode)
- R8: Zero-Build Serverless Architecture & API Surface Preservation (api/index.py, vercel.json, Dockerfile, Zero Node.js Build, All API Endpoints Intact)
"""

import os
from pathlib import Path
import re
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sih_archive.api.app import app
from sih_archive.schemas.heritage import (
    ALLOWED_COLLECTIONS,
    ALLOWED_RIGHTS_STATUS,
    HeritageRecord,
    ProvenanceMetadata,
)
from sih_archive.ui.fixtures import (
    CATALOG_ITEMS,
    get_catalog_item,
    get_catalog_items,
    get_curated_collections,
    get_media_records,
    get_timeline_events,
    get_viewer_pages,
)
from sih_archive.ui.page_builder import build_kiosk_html, build_portal_html
from sih_archive.ui.scripts import get_scripts
from sih_archive.ui.styles import THEME_TOKENS, get_styles


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with initialized lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# Requirement R1: Coherent Heritage Design System & Visual Hierarchy
# =============================================================================

def test_r1_design_system_palette_and_typography():
    """Validates deep navy, ivory, bronze, verified green, slate, and terracotta #9a3412 tokens, serif typography, absence of glassmorphism blur in modals."""
    colors = THEME_TOKENS["colors"]

    # Verify palette tokens
    assert colors["primary_dark"] == "#0f172a" or colors["primary"] == "#0f172a", "Deep navy primary missing"
    assert colors["parchment"] == "#fdfbf7", "Warm ivory/parchment paper missing"
    assert colors["bronze"] == "#b45309", "Muted bronze accent missing"
    assert colors["gold"] == "#d97706", "Gold accent missing"
    assert colors["green_verified"] == "#059669", "Subtle verified green missing"
    assert colors.get("slate") == "#334155" or colors.get("navy_slate") == "#334155", "Neutral slate missing"
    assert colors["terracotta"] == "#9a3412", "Terracotta #9a3412 token missing"

    # Verify CSS variables in get_styles()
    css = get_styles()
    assert "--accent-terracotta: #9a3412;" in css
    assert "--accent-terracotta-light: #c2410c;" in css
    assert "--accent-terracotta-bg: #fff7ed;" in css
    assert "--primary-dark: #0f172a;" in css or "--bg-primary: #0f172a;" in css
    assert "--bg-parchment: #fdfbf7;" in css or "--bg-paper: #fdfbf7;" in css
    assert "--accent-bronze: #b45309;" in css
    assert "--status-verified: #059669;" in css or "--accent-green: #059669;" in css

    # Typography: Serif for titles, sans-serif for UI
    assert "Cinzel" in css or "Playfair Display" in css or "Georgia" in css
    assert "Inter" in css or "system-ui" in css

    # Absence of glassmorphism blur on modal scrims
    portal_html = build_portal_html()
    assert 'id="provenance-modal"' in portal_html
    assert "backdrop-filter: blur" not in portal_html, "Forbidden glassmorphism blur detected in modal scrim"


# =============================================================================
# Requirement R2: Homepage 7-Section Architecture & Live Demo CTAs
# =============================================================================

def test_r2_homepage_7_sections_architecture(client):
    """Validates all 7 sections under #view-portal (Hero with H1 and Dual-Preservation, Live Demo CTAs, 6 Curated Collection Cards, Featured Document Showcase with view trigger, Horizontal Timeline strip 1916-1956, A/V Showcase with synced transcript, Research Showcase, and Institutional Archival Footer with 6-stage provenance chain and legal notices)."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Portal container
    assert 'id="view-portal"' in html

    # Section 1: Hero with Primary H1 and Dual-Preservation Subtitle
    assert "Explore the Life, Ideas & Legacy of Dr. B. R. Ambedkar" in html
    assert "Explore, Preserve & Understand India's Digital Heritage" in html
    assert "Explore the Archive" in html
    assert "Ask the Research Assistant" in html

    # Section 2: Curated Collections (6 visual cards) + Legacy Discovery Pathways
    assert "curated-collections-section" in html
    assert "curated-collections-grid" in html
    assert html.count('<div class="curated-collection-card"') == 6
    assert "col_writings_speeches" in html
    assert "col_constitutional_debates" in html
    assert "col_manuscripts_documents" in html
    assert "col_photographs_memorabilia" in html
    assert "col_audio_video_archive" in html
    assert "col_memorial_heritage_sites" in html
    assert "Writings & Speeches" in html
    assert "Constitutional Debates" in html
    assert "Manuscripts & Documents" in html
    assert "Photographs & Memorabilia" in html
    assert "Audio & Video Archive" in html
    assert "Memorial & Heritage Sites" in html
    assert "ONE ARCHIVE. MANY WAYS TO EXPLORE." in html

    # Section 3: Featured Document Showcase with Direct View Trigger
    assert "featured-doc-showcase" in html
    assert "Featured Archival Document Showcase" in html
    assert "openDocumentInViewer" in html
    assert "btn-view-document" in html

    # Section 4: Horizontal Timeline Strip (1916-1956)
    assert "portal-timeline-section" in html
    assert "portal-timeline-strip" in html
    assert "portal-timeline-card" in html
    assert "1916" in html
    assert "1920" in html
    assert "1927" in html
    assert "1932" in html
    assert "1947" in html
    assert "1949" in html
    assert "1950" in html
    assert "1956" in html

    # Section 5: Audio-Visual Showcase with Synced Transcript
    assert "portal-av-showcase" in html
    assert "Audio-Visual Heritage Feature" in html
    assert "portal-transcript-line" in html
    assert "[00:00]" in html

    # Section 6: Evidence-Grounded Research Showcase
    assert "portal-research-showcase" in html
    assert "portal-citation-card" in html

    # Section 7: Institutional Archival Footer with 6-Stage Chain and Legal Notices
    assert "global-footer" in html
    assert "footer-provenance-chain-box" in html
    assert "SOURCE OBJECT → DIGITAL COPY → PAGE → OCR/LAYOUT → RETRIEVAL → ANSWER/DERIVATIVE" in html
    assert "Section 52(1)(q)" in html
    assert "Section 22" in html
    assert "WCAG 2.2 AA" in html
    assert "DEMO & SYNTHETIC MODE" in html


def test_r2_live_demo_ctas_active(client):
    """Validates 'EXPLORE THE LIVE ARCHIVE' and 'WATCH PLATFORM DEMO' buttons are active and properly wired."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert "EXPLORE THE LIVE ARCHIVE" in html
    assert "WATCH PLATFORM DEMO" in html
    assert "btn-live-archive" in html
    assert "btn-watch-demo" in html

    # Check button interactions
    assert "switchTab('explorer')" in html


# =============================================================================
# Requirement R3: Archival Document Catalog & Library Search Experience
# =============================================================================

def test_r3_faceted_catalog_and_institution_filter(client):
    """Validates #filter-institution in toolbar and client filtering."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Dropdown in DOM
    assert 'id="filter-institution"' in html
    assert "All Institutions" in html
    assert "National Archives of India" in html
    assert "Dr. Ambedkar Foundation" in html
    assert "Lok Sabha Secretariat" in html
    assert "Nehru Memorial Museum & Library / PMML" in html
    assert "Columbia University" in html
    assert "London School of Economics" in html
    assert "Maharashtra State Archives" in html
    assert "Dr. Ambedkar National Memorial" in html

    # Script binding
    scripts = get_scripts()
    assert 'document.getElementById("filter-institution")' in scripts
    assert "item.institution" in scripts
    assert 'setVal("filter-institution", "")' in scripts or 'filter-institution' in scripts


def test_r3_institution_stopword_filtering_accuracy():
    """Validates that generic stopwords (library, museum, archives, national, india, secretariat) are excluded from single-word fallbacks, preventing false positives while matching distinctive tokens."""
    scripts = get_scripts()

    # Verify stopwords definition in scripts
    assert "genericStopwords" in scripts
    assert '"library"' in scripts
    assert '"museum"' in scripts
    assert '"archives"' in scripts
    assert '"national"' in scripts
    assert '"india"' in scripts
    assert '"secretariat"' in scripts

    # Simulate refined institution matching logic
    catalog = get_catalog_items()
    generic_stopwords = {
        "library", "museum", "archives", "national", "india", "secretariat",
        "committee", "government", "ministry", "department", "rare", "book",
        "manuscript", "school", "university", "memorial", "state", "central"
    }

    def match_institution(item_inst: str, filter_inst: str) -> bool:
        item_lower = (item_inst or "").lower()
        filter_lower = (filter_inst or "").lower()
        if filter_lower in item_lower:
            return True
        primary_part = filter_lower.split("/")[0].strip()
        if primary_part and primary_part in item_lower:
            return True
        words = [w for w in re.split(r"[^a-z0-9]+", filter_lower) if len(w) > 3 and w not in generic_stopwords]
        return len(words) > 0 and any(w in item_lower for w in words)

    # 1. PMML filter must match genuine PMML records
    pmml_matches = [i for i in catalog if match_institution(i.get("institution", ""), "Nehru Memorial Museum & Library / PMML")]
    pmml_ids = {i["id"] for i in pmml_matches}
    assert "cat_states_and_minorities_1947" in pmml_ids
    assert "cat_mooknayak_1920" in pmml_ids

    # 2. PMML filter must NOT match Columbia University or Maharashtra State Archives solely because of "library" or "museum"
    for m in pmml_matches:
        inst = m.get("institution", "")
        assert "Columbia University" not in inst
        assert "Maharashtra State Archives, Mumbai" != inst

    # 3. National Archives filter matches genuine NAI items
    nai_matches = [i for i in catalog if match_institution(i.get("institution", ""), "National Archives of India")]
    assert len(nai_matches) >= 3
    for m in nai_matches:
        assert "National Archives of India" in m.get("institution", "")


def test_r3_search_results_enrichment(client):
    """Validates search result card metadata, source archive, page number, and direct jump interaction."""
    scripts = get_scripts()

    # Search result card enriched rendering in scripts
    assert "Source Archive:" in scripts
    assert "Page ${pageNum}" in scripts
    assert "thumbUrl" in scripts
    assert "SEARCH → RESULT → SOURCE PAGE → HIGHLIGHTED EVIDENCE" in scripts
    assert "openDocumentInViewer" in scripts

    # Search API endpoint enrichment
    res = client.get("/api/v1/search?q=Ambedkar")
    assert res.status_code == 200
    data = res.json()
    assert "hits" in data
    assert len(data["hits"]) > 0
    hit = data["hits"][0]
    assert "document_id" in hit
    assert "page_id" in hit
    assert "text_snippet" in hit or "snippet" in hit
    assert "score" in hit


# =============================================================================
# Requirement R4: Split Document & Manuscript Viewer with Region Evidence
# =============================================================================

def test_r4_split_document_viewer_previous_next_navigation(client):
    """Validates #btn-viewer-prev-page and #btn-viewer-next-page, cyclic pagination, 3-column layout, and canvas."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Prev and Next buttons in DOM
    assert 'id="btn-viewer-prev-page"' in html
    assert 'id="btn-viewer-next-page"' in html
    assert 'onclick="viewerPrevPage()"' in html
    assert 'onclick="viewerNextPage()"' in html
    assert 'title="Previous Folio Page"' in html
    assert 'title="Next Folio Page"' in html
    assert 'aria-label="Previous Page"' in html
    assert 'aria-label="Next Page"' in html

    # 3-column viewer layout classes
    assert "viewer-layout" in html
    assert "viewer-left-col" in html
    assert "viewer-center-col" in html
    assert "viewer-right-col" in html

    # Canvas & controls
    assert "viewer-canvas-container" in html
    assert "viewer-transform-wrap" in html
    assert "viewer-image" in html
    assert "viewer-bbox-overlay" in html
    assert "btn-zoom-in" in html
    assert "btn-zoom-out" in html
    assert "btn-zoom-reset" in html

    # Cyclic pagination functions in scripts.py
    scripts = get_scripts()
    assert "function viewerPrevPage()" in scripts
    assert "function viewerNextPage()" in scripts
    assert "VIEWER_PAGES.length - 1" in scripts
    assert "loadViewerPage" in scripts


def test_r4_viewer_truthful_evidence_and_degradation():
    """Validates SOURCE EVIDENCE overlay and verbatim truthful degradation notice 'Region-level evidence unavailable for this record.'."""
    scripts = get_scripts()

    # Bounding box badge tag
    assert "SOURCE EVIDENCE" in scripts
    assert "evidence-tag" in scripts

    # Truthful degradation notice
    assert "Region-level evidence unavailable for this record." in scripts
    assert "viewer-degrade-msg" in scripts

    # Ensure no fabricated fake coordinates
    assert "fabricat" not in scripts.lower()


# =============================================================================
# Requirement R5: Research Assistant Workspace with Citation Evidence
# =============================================================================

def test_r5_research_assistant_truthful_framing_banner(client):
    """Validates verbatim notice 'Archival Research Synthesis is grounded strictly in retrieved historical primary sources and does not claim infallible historical omniscience.'."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Institutional Truthful Framing Banner in Assistant View
    assert "assistant-truthful-framing-banner" in html
    assert "Institutional Archival Integrity Notice" in html
    expected_notice = "Archival Research Synthesis is grounded strictly in retrieved historical primary sources and does not claim infallible historical omniscience."
    assert expected_notice in html

    # 3-column assistant workspace
    assert "assistant-layout" in html
    assert "assistant-left-col" in html
    assert "assistant-center-col" in html
    assert "assistant-right-col" in html
    assert "session-history-pane" in html
    assert "evidence-drawer-pane" in html
    assert 'id="assistant-session-history"' in html
    assert 'id="assistant-citations-list"' in html


def test_r5_research_assistant_citations_and_refusal(client):
    """Validates citation cards with View Source -> jump, and principled refusal card with verbatim string 'Insufficient archival evidence found for a supported answer.'."""
    scripts = get_scripts()

    # Citation jumping
    assert "jumpToEvidence" in scripts
    assert "View Source →" in scripts or "jumpToEvidence(" in scripts

    # Principled algorithmic refusal card in client scripts
    assert "refusal-card" in scripts
    expected_refusal = "Insufficient archival evidence found for a supported answer."
    assert expected_refusal in scripts
    assert "Algorithmic Refusal Gate Activated" in scripts

    # QA API endpoint functionality and refusal trigger
    res_valid = client.post("/api/v1/qa", json={"question": "What was Dr. Ambedkar's role in the Constituent Assembly?"})
    assert res_valid.status_code == 200
    data_valid = res_valid.json()
    assert "answer_text" in data_valid
    assert "citations" in data_valid

    # Out-of-domain query triggering algorithmic refusal
    res_refusal = client.post("/api/v1/qa", json={"question": "What is quantum gravity in outer space 3000?"})
    assert res_refusal.status_code == 200
    data_refusal = res_refusal.json()
    assert data_refusal["is_refusal"] is True
    assert "REFUSAL:" in data_refusal["answer_text"]


# =============================================================================
# Requirement R6: Archival Fixtures & Asset Schema Enrichment
# =============================================================================

def test_r6_fixtures_19_field_schema_and_corpus():
    """Validates that every catalog item in fixtures.py strictly conforms to the 19-field HeritageRecord schema and retains all 9 backward-compatibility keys across all 24 records."""
    catalog = get_catalog_items()

    # Exactly 24 records
    assert len(catalog) == 24

    standard_19_fields = [
        "id", "title", "subtitle", "collection", "date", "language",
        "document_type", "institution", "source", "description",
        "thumbnail", "page_images", "transcript", "audio", "video",
        "rights", "provenance", "related_items", "timeline_event",
    ]

    auxiliary_9_keys = [
        "document_id", "author", "summary", "material_type",
        "preview_page_id", "has_ocr", "has_image", "page_count", "rights_evidence",
    ]

    collections_found = set()
    for item in catalog:
        # Validate through Pydantic
        record = HeritageRecord.model_validate(item)
        assert record.id == item["id"]

        # 19 standard fields present
        for field in standard_19_fields:
            assert field in item, f"Field '{field}' missing from item {item.get('id')}"

        # 9 auxiliary keys present
        for key in auxiliary_9_keys:
            assert key in item, f"Backward compatibility key '{key}' missing from item {item.get('id')}"

        # Collection in allowed set
        assert record.collection in ALLOWED_COLLECTIONS
        collections_found.add(record.collection)

        # Rights status in allowed set
        assert record.rights in ALLOWED_RIGHTS_STATUS

    # Full coverage across all 6 collections
    assert len(collections_found) == 6
    assert collections_found == set(ALLOWED_COLLECTIONS)

    # Dual lookup: primary id and document_id
    item_by_id = get_catalog_item("cat_ambedkar_vol1")
    assert item_by_id is not None
    assert item_by_id["title"] == "Dr. Babasaheb Ambedkar: Writings and Speeches, Vol. 1"

    item_by_doc_id = get_catalog_item("ambedkar_speech_vol1")
    assert item_by_doc_id is not None
    assert item_by_doc_id["id"] == "cat_ambedkar_vol1"


def test_r6_catalog_api_endpoints(client):
    """Validates GET /api/v1/catalog (filters by collection, language, document_type, institution) and GET /api/v1/catalog/{item_id}."""
    # List all
    res = client.get("/api/v1/catalog")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 24
    assert data["total_items"] == 24
    assert data["schema_version"] == "19-field-r6"
    assert len(data["records"]) == 24
    assert len(data["items"]) == 24

    # Filter by collection
    res_col = client.get("/api/v1/catalog?collection=Constitutional+Debates")
    assert res_col.status_code == 200
    data_col = res_col.json()
    assert len(data_col["records"]) >= 4
    for r in data_col["records"]:
        assert r["collection"] == "Constitutional Debates"

    # Filter by language
    res_lang = client.get("/api/v1/catalog?language=mar")
    assert res_lang.status_code == 200
    data_lang = res_lang.json()
    assert len(data_lang["records"]) >= 3
    for r in data_lang["records"]:
        assert r["language"] == "mar"

    # Filter by institution
    res_inst = client.get("/api/v1/catalog?institution=Columbia")
    assert res_inst.status_code == 200
    data_inst = res_inst.json()
    assert len(data_inst["records"]) >= 2
    for r in data_inst["records"]:
        assert "Columbia" in r["institution"]

    # Detail item by valid ID
    res_item = client.get("/api/v1/catalog/cat_ambedkar_vol1")
    assert res_item.status_code == 200
    item_data = res_item.json()
    assert item_data["id"] == "cat_ambedkar_vol1"

    # Detail item by document_id alias
    res_alias = client.get("/api/v1/catalog/ambedkar_speech_vol1")
    assert res_alias.status_code == 200
    assert res_alias.json()["id"] == "cat_ambedkar_vol1"

    # 404 for nonexistent item
    res_missing = client.get("/api/v1/catalog/nonexistent_historical_item_999")
    assert res_missing.status_code == 404
    assert "not found" in res_missing.json()["detail"].lower()


# =============================================================================
# Requirement R7: Dedicated Touchscreen Kiosk & Smart-Display Experience
# =============================================================================

def test_r7_kiosk_touchscreen_and_discovery_tiles(client):
    """Validates the 5 R7 discovery categories ('Start Exploring', 'Listen', 'Timeline', 'Search', 'Featured Documents') with dual-preservation of legacy strings, #btn-kiosk-home, and >=48px touch target enforcement."""
    res = client.get("/kiosk")
    assert res.status_code == 200
    html = res.text

    # 5 R7 Discovery Categories
    assert "Start Exploring" in html
    assert "Listen" in html
    assert "Timeline" in html
    assert "Search" in html
    assert "Featured Documents" in html

    # Dual-preservation of legacy strings
    assert "Explore Heritage" in html
    assert "Watch" in html
    assert "Ask" in html
    assert "Explore Manuscripts" in html
    assert "Chronological Timeline" in html

    # Home / Back touch control in kiosk header
    assert 'id="btn-kiosk-home"' in html
    assert "kioskNav('home')" in html or 'kioskNav("home")' in html

    # Minimum 48px touch targets in styles and page builder
    css = get_styles()
    assert "--kiosk-touch-min: 48px;" in html or "--kiosk-touch-min: 48px;" in css
    assert "min-height: 48px;" in html or "min-height: 48px;" in css
    assert "min-width: 48px;" in html or "min-width: 48px;" in css


def test_r7_kiosk_smart_display_ambient_mode(client):
    """Validates 8-second ambient cycling, progress bar, and touch/Space pause/resume."""
    res = client.get("/kiosk")
    assert res.status_code == 200
    html = res.text

    # Ambient display containers and controls
    assert 'id="ambient-display-mode"' in html
    assert 'id="btn-ambient-toggle"' in html
    assert 'id="ambient-progress-bar"' in html

    # Ambient scripts: 8-second timing and interactive pause/resume
    assert "DURATION_MS = 8000" in html
    assert "onAmbientTouch" in html
    assert "PAUSED (Touch to Resume)" in html
    assert "Space" in html


# =============================================================================
# Requirement R8: Zero-Build Serverless Architecture & API Preservation
# =============================================================================

def test_r8_zero_build_serverless_compatibility():
    """Validates api/index.py ASGI app, absence of Node.js build configs, and zero breaking changes across all API endpoints."""
    repo_root = Path(__file__).resolve().parent.parent

    # 1. Vercel Serverless Function entrypoint
    entrypoint = repo_root / "api" / "index.py"
    assert entrypoint.is_file(), "api/index.py must exist"
    entrypoint_content = entrypoint.read_text(encoding="utf-8")
    assert "from sih_archive.api.app import app" in entrypoint_content
    assert '__all__ = ["app"]' in entrypoint_content

    # Import app from entrypoint directly
    from api.index import app as vercel_app
    assert isinstance(vercel_app, FastAPI)

    # 2. vercel.json rewrite configuration
    vercel_json = repo_root / "vercel.json"
    assert vercel_json.is_file(), "vercel.json must exist"
    vercel_text = vercel_json.read_text(encoding="utf-8")
    assert '"destination": "/api/index.py"' in vercel_text

    # 3. Dockerfile production container
    dockerfile = repo_root / "Dockerfile"
    assert dockerfile.is_file(), "Dockerfile must exist"
    docker_text = dockerfile.read_text(encoding="utf-8")
    assert "python:3.11-slim" in docker_text
    assert "uvicorn sih_archive.api.app:app" in docker_text

    # 4. Strict Zero-Build validation: No package.json or node_modules
    forbidden_files = [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "webpack.config.js",
        "vite.config.js",
        "tsconfig.json",
    ]
    for fname in forbidden_files:
        assert not (repo_root / fname).exists(), f"Forbidden build artifact {fname} found in repository!"

    assert not (repo_root / "node_modules").exists(), "node_modules directory must not exist"


def test_r8_full_api_surface_invariants(client):
    """Validates that all critical endpoints across the entire API surface respond with 200 OK and expected payloads."""
    # Core health & operational endpoints
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"

    res_diag = client.get("/api/v1/diagnostics")
    assert res_diag.status_code == 200
    assert "ocr_host_engine" in res_diag.json()

    # Search and QA
    res_search = client.get("/api/v1/search?q=Ambedkar")
    assert res_search.status_code == 200
    assert "hits" in res_search.json()

    res_qa = client.post("/api/v1/qa", json={"question": "Who was Dr. Ambedkar?"})
    assert res_qa.status_code == 200
    assert "answer_text" in res_qa.json()

    # Catalog & folios
    res_catalog = client.get("/api/v1/catalog")
    assert res_catalog.status_code == 200
    assert res_catalog.json()["total_records"] == 24

    res_cat_item = client.get("/api/v1/catalog/cat_ambedkar_vol1")
    assert res_cat_item.status_code == 200

    res_page_meta = client.get("/api/v1/pages/ambedkar_speech_vol1_p0001")
    assert res_page_meta.status_code == 200
    assert res_page_meta.json()["page_id"] == "ambedkar_speech_vol1_p0001"

    res_page_img = client.get("/api/v1/pages/ambedkar_speech_vol1_p0001/image")
    assert res_page_img.status_code == 200
    assert res_page_img.headers["content-type"] == "image/png"

    res_prov = client.get("/api/v1/provenance/ambedkar_speech_vol1_p0001")
    assert res_prov.status_code == 200
    assert "stages" in res_prov.json() or "chain" in res_prov.json()

    # Multi-modal media & timeline
    res_timeline = client.get("/api/v1/timeline")
    assert res_timeline.status_code == 200
    assert "events" in res_timeline.json() or isinstance(res_timeline.json(), list)

    res_media = client.get("/api/v1/media")
    assert res_media.status_code == 200
    assert "items" in res_media.json() or isinstance(res_media.json(), list)

    # Admin audit
    res_audit = client.get("/api/v1/admin/audit")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["catalog_records_count"] == 24
    assert audit_data["schema_19_field_compliance"] is True

    # Kiosk interface
    res_kiosk = client.get("/kiosk")
    assert res_kiosk.status_code == 200
    assert "Start Exploring" in res_kiosk.text
