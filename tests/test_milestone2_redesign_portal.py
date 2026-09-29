"""
Automated Verification Suite for Milestone 2:
Homepage 7-Section Architecture, Live Demo CTAs, Curated Collection Cards,
Featured Document Showcase, Timeline Strip, A/V Showcase, Research Showcase,
Institutional Footer, and Faceted Catalog Search with Institution Filter.
"""

import pytest
from fastapi.testclient import TestClient

from sih_archive.api.app import app
from sih_archive.ui.fixtures import (
    CURATED_COLLECTIONS,
    get_curated_collections,
)
from sih_archive.ui.page_builder import build_portal_html
from sih_archive.ui.scripts import get_scripts
from sih_archive.ui.styles import get_styles


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with initialized lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Hero Section, Eyebrow & Dual-Preserved Actions
# -----------------------------------------------------------------------------

def test_portal_hero_headline_and_subtitles(client):
    """Verify primary H1 headline, eyebrow, and institutional subtitle in Hero section."""
    res = client.get("/")
    assert res.status_code == 200
    text = res.text

    # Primary H1 headline for Dr. B. R. Ambedkar
    assert "Explore the Life, Ideas & Legacy of Dr. B. R. Ambedkar" in text
    assert "<h1" in text

    # Dual-preservation subtext / eyebrow
    assert "Explore, Preserve & Understand India's Digital Heritage" in text
    assert (
        "A provenance-linked institutional archive connecting manuscripts, documents, "
        "photographs, audio-visual heritage and evidence-grounded research." in text
    )


def test_portal_hero_action_buttons(client):
    """Verify primary actions and legacy action links are present."""
    res = client.get("/")
    text = res.text

    # Primary Actions
    assert "Explore Archive" in text
    assert "Search Archive" in text
    assert "Research Assistant" in text

    # Dual-Preservation Legacy Action Strings
    assert "Explore the Archive" in text
    assert "Ask the Research Assistant" in text


def test_portal_live_demo_ctas(client):
    """Verify prominent Live Demo CTAs (EXPLORE THE LIVE ARCHIVE & WATCH PLATFORM DEMO)."""
    res = client.get("/")
    text = res.text

    assert "EXPLORE THE LIVE ARCHIVE" in text
    assert "btn-live-archive" in text
    assert "WATCH PLATFORM DEMO" in text
    assert "btn-watch-demo" in text
    assert 'target="_blank"' in text


# -----------------------------------------------------------------------------
# 2. Curated Collections (6 Cards) & Dual-Preservation Pathways
# -----------------------------------------------------------------------------

def test_curated_collections_fixtures():
    """Verify CURATED_COLLECTIONS contains 6 valid collections with required fields."""
    collections = get_curated_collections()
    assert len(collections) == 6
    assert len(CURATED_COLLECTIONS) == 6

    expected_titles = [
        "Writings & Speeches",
        "Constitutional Debates",
        "Manuscripts & Documents",
        "Photographs & Memorabilia",
        "Audio & Video Archive",
        "Memorial & Heritage Sites",
    ]
    for c in collections:
        assert c["title"] in expected_titles
        assert c["item_count"] > 0
        assert "Verified Records" in c["verified_count_label"] or "Media Items" in c["verified_count_label"]
        assert c["thumbnail"].startswith("/api/v1/pages/")
        assert len(c["description"]) > 20


def test_portal_curated_collections_rendered(client):
    """Verify all 6 Curated Collection Cards are rendered on the homepage."""
    res = client.get("/")
    text = res.text

    assert "Curated Archival Collections" in text
    assert "curated-collections-grid" in text
    assert "col_writings_speeches" in text
    assert "col_constitutional_debates" in text
    assert "col_manuscripts_documents" in text
    assert "col_photographs_memorabilia" in text
    assert "col_audio_video_archive" in text
    assert "col_memorial_heritage_sites" in text

    # Verification of item count badges
    assert "Verified Records" in text


def test_portal_dual_preservation_pathways_and_treasures(client):
    """Verify legacy discovery pathways and featured treasures remain intact."""
    res = client.get("/")
    text = res.text

    assert "ONE ARCHIVE. MANY WAYS TO EXPLORE." in text
    assert "Manuscripts & Books" in text or "Manuscripts &amp; Books" in text
    assert "Documents & Debates" in text or "Documents &amp; Debates" in text
    assert "Photographs & Records" in text or "Photographs &amp; Records" in text
    assert "Audio & Video" in text or "Audio &amp; Video" in text
    assert "Timelines & Stories" in text or "Timelines &amp; Stories" in text
    assert "Research Assistant" in text
    assert "Featured Archival Treasures" in text


# -----------------------------------------------------------------------------
# 3. Featured Document Showcase
# -----------------------------------------------------------------------------

def test_portal_featured_document_showcase(client):
    """Verify Featured Document Showcase component with metadata and View Document trigger."""
    res = client.get("/")
    text = res.text

    assert "featured-doc-showcase" in text
    assert "Featured Archival Document Showcase" in text
    assert "300 DPI MASTER SCAN" in text
    assert "Constituent Assembly Debates: Motion Introducing Draft Constitution" in text
    assert "Lok Sabha Secretariat / Dr. Ambedkar Foundation / National Archives of India" in text
    assert "November 4, 1948" in text
    assert "btn-view-document" in text
    assert "View Document" in text
    assert "openDocumentInViewer('ambedkar_speech_vol1', 'ambedkar_speech_vol1_p0001')" in text


# -----------------------------------------------------------------------------
# 4. Explore by Time (Horizontal Timeline Strip)
# -----------------------------------------------------------------------------

def test_portal_horizontal_timeline_strip(client):
    """Verify Explore by Time horizontal chronological strip."""
    res = client.get("/")
    text = res.text

    assert "portal-timeline-section" in text
    assert "Explore by Time: Historical Milestones (1916–1956)" in text
    assert "portal-timeline-strip" in text
    assert "portal-timeline-card" in text
    assert "portal-timeline-year-pill" in text
    assert "1916" in text
    assert "1956" in text
    assert "btn-timeline-inspect" in text


# -----------------------------------------------------------------------------
# 5. Audio-Visual Feature Showcase
# -----------------------------------------------------------------------------

def test_portal_audio_visual_feature_showcase(client):
    """Verify dedicated Audio-Visual showcase with metadata and synchronized transcript preview."""
    res = client.get("/")
    text = res.text

    assert "portal-av-showcase" in text
    assert "Audio-Visual Heritage Feature" in text
    assert "BBC Radio Interview with Dr. B. R. Ambedkar" in text
    assert "03:45 Duration" in text
    assert "Dr. B. R. Ambedkar with Francis Watson" in text
    assert "portal-transcript-line" in text
    assert "[00:00]" in text
    assert "[00:32]" in text
    assert "[01:15]" in text
    assert "Listen in Studio" in text


# -----------------------------------------------------------------------------
# 6. Evidence-Grounded Research Showcase
# -----------------------------------------------------------------------------

def test_portal_evidence_grounded_research_showcase(client):
    """Verify Research Assistant showcase with sample inquiry, answer, and primary source citations."""
    res = client.get("/")
    text = res.text

    assert "portal-research-showcase" in text
    assert "Evidence-Grounded Research Showcase" in text
    assert "Did the Education Department, Government of Maharashtra publish" in text
    assert "VERIFIED PRIMARY SOURCE ATTRIBUTION" in text
    assert "Citation [1]" in text
    assert "ambedkar_speech_vol1_p0001" in text
    assert "Inspect Folio Evidence ↗" in text


# -----------------------------------------------------------------------------
# 7. Institutional Archival Footer
# -----------------------------------------------------------------------------

def test_portal_institutional_archival_footer(client):
    """Verify institutional footer with attributions, provenance, accessibility, rights, and disclaimers."""
    res = client.get("/")
    text = res.text

    assert "global-footer" in text
    # 6-Stage Provenance Summary
    assert "SOURCE OBJECT → DIGITAL COPY → PAGE → OCR/LAYOUT → RETRIEVAL → ANSWER/DERIVATIVE" in text

    # Source Holdings Attributions
    assert "National Archives of India" in text
    assert "Dr. Ambedkar Foundation" in text
    assert "Lok Sabha Secretariat" in text
    assert "Nehru Memorial Museum & Library / PMML" in text
    assert "Columbia University" in text
    assert "London School of Economics" in text
    assert "Maharashtra State Archives" in text

    # Statutory Rights
    assert "Indian Copyright Act 1957 Section 52(1)(q)" in text
    assert "Indian Copyright Act 1957 Section 22" in text

    # Accessibility Standards
    assert "WCAG 2.2 AA Compliance" in text

    # Demo & Synthetic Mode Disclaimer
    assert "DEMO & SYNTHETIC MODE" in text or "DEMO &amp; SYNTHETIC MODE" in text


# -----------------------------------------------------------------------------
# 8. Catalog Search & Institution Filter
# -----------------------------------------------------------------------------

def test_catalog_institution_filter_dropdown(client):
    """Verify #filter-institution is populated with all major source institutions."""
    res = client.get("/")
    text = res.text

    assert 'id="filter-institution"' in text
    assert "All Institutions" in text
    assert "National Archives of India" in text
    assert "Dr. Ambedkar Foundation" in text
    assert "Lok Sabha Secretariat" in text
    assert "Nehru Memorial Museum & Library / PMML" in text
    assert "Columbia University" in text
    assert "London School of Economics" in text
    assert "Maharashtra State Archives" in text
    assert "Dr. Ambedkar National Memorial" in text


def test_scripts_institution_filter_and_search_enrichment():
    """Verify get_scripts() includes institution filter handling and search hit card enrichment."""
    scripts = get_scripts()

    # Filter institution binding
    assert 'document.getElementById("filter-institution")' in scripts
    assert 'item.institution' in scripts

    # Search result card enrichment
    assert "Source Archive:" in scripts
    assert "Page ${pageNum}" in scripts
    assert "thumbUrl" in scripts
    assert "SEARCH → RESULT → SOURCE PAGE → HIGHLIGHTED EVIDENCE" in scripts


# -----------------------------------------------------------------------------
# 9. Stylesheet Rules for Milestone 2 Components
# -----------------------------------------------------------------------------

def test_styles_milestone2_css_rules():
    """Verify get_styles() contains all Milestone 2 CSS component classes."""
    css = get_styles()

    assert ".btn-live-archive" in css
    assert ".btn-watch-demo" in css
    assert ".curated-collections-grid" in css
    assert ".curated-collection-card" in css
    assert ".featured-doc-showcase" in css
    assert ".btn-view-document" in css
    assert ".portal-timeline-strip" in css
    assert ".portal-av-showcase" in css
    assert ".portal-research-showcase" in css
    assert ".footer-provenance-chain-box" in css
