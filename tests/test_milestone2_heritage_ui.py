"""
Automated Verification Suite for Milestone 2: Heritage Design System, Digital Portal & Archive Explorer.

Verifies:
- Museum/library-grade color tokens and typography in styles.py
- Complete Digital Heritage Portal (GET /) hero, discovery pathways, featured treasures
- Multi-faceted Archive Explorer filtering toolbar and catalog cards
- Evidence-grounded search with mode selector (hybrid, bm25, ngram, dense)
- Direct jump interaction contract (SEARCH -> RESULT -> SOURCE PAGE -> HIGHLIGHTED EVIDENCE)
- Search endpoint alias support for 'mode' parameter (?q=...&mode=hybrid)
- Complete preservation of all critical invariants
"""

import pytest
from fastapi.testclient import TestClient

from sih_archive.api.app import app
from sih_archive.ui.fixtures import (
    get_catalog_items,
    get_discovery_pathways,
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
# 1. Heritage Design System & Styles Tests
# -----------------------------------------------------------------------------

def test_heritage_design_system_theme_tokens():
    """Verify THEME_TOKENS specifies all required museum-grade colors and typography."""
    colors = THEME_TOKENS["colors"]
    assert colors["primary_dark"] == "#0f172a"
    assert colors["primary"] == "#1e293b"
    assert colors["parchment"] == "#fdfbf7"
    assert colors["ivory"] == "#f8fafc"
    assert colors["bronze"] == "#b45309"
    assert colors["gold"] == "#d97706"
    assert colors["green_verified"] == "#059669"
    assert colors["graphite"] == "#334155"
    assert colors["alert_red"] == "#b91c1c"

    typography = THEME_TOKENS["typography"]
    assert "Cinzel" in typography["heading_serif"]
    assert "Inter" in typography["body_sans"]
    assert "mono" in typography


def test_heritage_styles_css_rules():
    """Verify get_styles() generates CSS rules for banner, header, hero, pathways, and direct jump."""
    css = get_styles()
    assert "--primary-dark: #0f172a;" in css
    assert "--bg-parchment: #fdfbf7;" in css
    assert "--accent-bronze: #b45309;" in css
    assert ".demo-banner" in css
    assert ".global-header" in css
    assert ".nav-tab" in css
    assert ".portal-hero" in css
    assert ".pathway-card" in css
    assert ".catalog-card" in css
    assert ".btn-evidence-jump" in css


# -----------------------------------------------------------------------------
# 2. Digital Heritage Portal (GET /) Core Content & Invariants Tests
# -----------------------------------------------------------------------------

def test_portal_route_returns_200_and_invariants(client):
    """Verify GET / returns 200, HTML, and mandatory invariant strings."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    text = res.text

    # Invariants
    assert "DEMO & SYNTHETIC MODE" in text or "DEMO &amp; SYNTHETIC MODE" in text
    assert "Resilient Document Retrieval" in text

    # Global institutional header
    assert "TEAM ORBIT — National Digital Heritage Infrastructure" in text
    assert "/kiosk" in text

    # Navigation tabs
    assert 'data-tab="portal"' in text
    assert 'data-tab="explorer"' in text
    assert 'data-tab="viewer"' in text
    assert 'data-tab="assistant"' in text
    assert 'data-tab="timeline"' in text
    assert 'data-tab="media"' in text
    assert 'data-tab="admin"' in text


def test_portal_hero_and_ctas(client):
    """Verify Hero section copy, subtitles, and CTAs match specifications."""
    res = client.get("/")
    text = res.text

    # Headline & Subtitle
    assert "Explore, Preserve &amp; Understand India&#x27;s Digital Heritage" in text or "Explore, Preserve & Understand India's Digital Heritage" in text
    assert "A provenance-linked institutional archive connecting manuscripts, documents, photographs, audio-visual heritage and evidence-grounded research." in text

    # Primary and Secondary CTAs
    assert "Explore the Archive" in text
    assert "Ask the Research Assistant" in text

    # Institutional Stat Counters
    assert "5,420+" in text
    assert "100%" in text
    assert "16" in text


def test_discovery_pathways_rendered(client):
    """Verify all 6 Discovery Pathways are present with required headings."""
    res = client.get("/")
    text = res.text

    assert "ONE ARCHIVE. MANY WAYS TO EXPLORE." in text
    assert "Manuscripts &amp; Books" in text or "Manuscripts & Books" in text
    assert "Documents &amp; Debates" in text or "Documents & Debates" in text
    assert "Photographs &amp; Records" in text or "Photographs & Records" in text
    assert "Audio &amp; Video" in text or "Audio & Video" in text
    assert "Timelines &amp; Stories" in text or "Timelines & Stories" in text
    assert "Research Assistant" in text


def test_featured_archival_treasures_rendered(client):
    """Verify Featured Archival Treasures card section displays key historical records."""
    res = client.get("/")
    text = res.text

    assert "Featured Archival Treasures" in text
    assert "Dr. Babasaheb Ambedkar: Writings and Speeches, Vol. 1" in text
    assert "Annihilation of Caste with a Reply to Mahatma Gandhi" in text
    assert "Constituent Assembly Debates: Motion Introducing Draft Constitution" in text


# -----------------------------------------------------------------------------
# 3. Archive Explorer & Evidence-Grounded Search Tests
# -----------------------------------------------------------------------------

def test_archive_explorer_faceted_controls(client):
    """Verify Faceted browsing controls include collection, language, material, rights, era, keyword."""
    res = client.get("/")
    text = res.text

    assert 'id="filter-search"' in text
    assert 'id="filter-collection"' in text
    assert 'id="filter-language"' in text
    assert 'id="filter-material"' in text
    assert 'id="filter-rights"' in text
    assert 'id="filter-era"' in text
    assert 'id="catalog-grid"' in text


def test_evidence_grounded_search_interface(client):
    """Verify Evidence-Grounded Search section structure and mode selector."""
    res = client.get("/")
    text = res.text

    assert 'id="search-input"' in text
    assert 'id="search-engine"' in text
    assert 'value="hybrid"' in text
    assert 'value="bm25"' in text
    assert 'value="ngram"' in text
    assert 'value="dense"' in text
    assert 'id="search-results"' in text
    assert 'id="search-metrics"' in text


# -----------------------------------------------------------------------------
# 4. Search API 'mode' Query Parameter Alias Tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("mode_name", ["hybrid", "bm25", "ngram", "dense"])
def test_search_api_mode_parameter_support(client, mode_name):
    """Verify GET /api/v1/search?q={query}&mode={mode} operates identically to engine={engine}."""
    res = client.get(f"/api/v1/search?q=Ambedkar&mode={mode_name}&top_k=3")
    assert res.status_code == 200
    data = res.json()
    assert "hits" in data
    assert "engine" in data
    assert len(data["hits"]) > 0
    assert data["query"] == "Ambedkar"


def test_search_api_invalid_mode_rejected(client):
    """Verify GET /api/v1/search rejects unsupported mode gracefully."""
    res = client.get("/api/v1/search?q=Ambedkar&mode=quantum_search")
    assert res.status_code == 400
    assert "not supported" in res.json()["detail"]


# -----------------------------------------------------------------------------
# 5. Client Scripts & Direct Jump Interaction Contract Tests
# -----------------------------------------------------------------------------

def test_scripts_contain_client_interactions():
    """Verify get_scripts() provides tab switching, faceted filter, search, jump, and QA routines."""
    scripts = get_scripts()
    assert "ARCHIVE_CATALOG" in scripts
    assert "function switchTab(" in scripts
    assert "function filterCatalog(" in scripts
    assert "function resetFilters(" in scripts
    assert "function executeSearch(" in scripts
    assert "function jumpToEvidence(" in scripts
    assert "function openDocumentInViewer(" in scripts
    assert "function loadViewerPage(" in scripts
    assert "function executeQA(" in scripts
    assert "SEARCH → RESULT → SOURCE PAGE → HIGHLIGHTED EVIDENCE" in scripts
    assert "Region-level evidence unavailable for this record." in scripts
