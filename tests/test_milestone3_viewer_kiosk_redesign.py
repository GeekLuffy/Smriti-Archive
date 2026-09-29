"""
Automated Verification Suite for Milestone 3 UI/UX Redesign:
Manuscript Viewer (R4), Research Assistant Workspace (R5), and Touchscreen Kiosk (R7).

Verifies:
1. Split Document & Manuscript Viewer (R4):
   - Explicit Previous Page (id="btn-viewer-prev-page") and Next Page (id="btn-viewer-next-page") controls.
   - viewerPrevPage() and viewerNextPage() JavaScript functions cycling through loaded folios.
   - 100% preservation of 3-column layout (viewer-layout, viewer-left-col, viewer-center-col, viewer-right-col).
   - Thumbnail strip with 5 folios, pan/zoom toolbar, canvas container, bounding-box overlay with SOURCE EVIDENCE tag.
   - Truthful degradation notice verbatim text: "Region-level evidence unavailable for this record."
2. Research Assistant Workspace (R5):
   - Prominent institutional Truthful Framing disclaimer banner with verbatim text:
     "Archival Research Synthesis is grounded strictly in retrieved historical primary sources and does not claim infallible historical omniscience."
   - 100% preservation of 3-column layout (assistant-layout, assistant-left-col, assistant-center-col, assistant-right-col).
   - Session history, citation tags (#WritingsAndSpeeches, #Constitution1950), persistent evidence drawer (assistant-citations-list).
   - Principled algorithmic refusal card with verbatim string: "Insufficient archival evidence found for a supported answer."
3. Dedicated Touchscreen Kiosk Experience (R7):
   - 5 R7 discovery categories: "Start Exploring", "Listen", "Timeline", "Search", "Featured Documents".
   - Dual-preservation of legacy strings: "Explore Heritage", "Search", "Timeline", "Listen", "Watch", "Ask", "Explore Manuscripts", "Chronological Timeline".
   - Prominent Home / Back touch control (id="btn-kiosk-home") with onclick="kioskNav('home')".
   - Minimum 48px touch target enforcement (--kiosk-touch-min: 48px;, min-height: 48px;, min-width: 48px;).
   - Smart Display Mode (ambient mode) with 8s cycling (DURATION_MS = 8000) and touch/Space pause-resume.
4. Advisory Fix:
   - Flexible institution filter matching in filterCatalog().
"""

import re
import pytest
from fastapi.testclient import TestClient

from sih_archive.api.app import app
from sih_archive.ui.fixtures import (
    get_catalog_items,
    get_viewer_pages,
)
from sih_archive.ui.page_builder import build_kiosk_html, build_portal_html
from sih_archive.ui.scripts import get_scripts
from sih_archive.ui.styles import get_styles


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with initialized lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. R4: Document & Manuscript Viewer Enhancements & Invariants
# -----------------------------------------------------------------------------

def test_viewer_previous_and_next_page_controls(client):
    """Verify explicit, accessible Previous and Next page controls in viewer toolbar."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Previous Page control
    assert 'id="btn-viewer-prev-page"' in html
    assert 'onclick="viewerPrevPage()"' in html
    assert "Prev Page" in html
    assert 'aria-label="Previous Page"' in html

    # Next Page control
    assert 'id="btn-viewer-next-page"' in html
    assert 'onclick="viewerNextPage()"' in html
    assert "Next Page" in html
    assert 'aria-label="Next Page"' in html

    # Adjacent to folio title in viewer toolbar
    assert 'id="viewer-page-title"' in html
    toolbar_idx = html.find('class="viewer-toolbar"')
    prev_idx = html.find('id="btn-viewer-prev-page"')
    title_idx = html.find('id="viewer-page-title"')
    next_idx = html.find('id="btn-viewer-next-page"')

    assert toolbar_idx < prev_idx < title_idx < next_idx


def test_viewer_scripts_pagination_functions():
    """Verify viewerPrevPage() and viewerNextPage() JavaScript functions exist and cycle correctly."""
    scripts = get_scripts()

    assert "function viewerPrevPage(" in scripts
    assert "function viewerNextPage(" in scripts

    # Cycling logic checks
    assert "VIEWER_PAGES.findIndex" in scripts
    assert "currentViewerPageId" in scripts
    assert "loadViewerPage" in scripts


def test_viewer_preserved_layout_and_evidence_invariants(client):
    """Verify 3-column layout, thumbnail strip, zoom tools, bounding box overlay, and degradation text."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    scripts = get_scripts()

    # 3-column layout classes
    assert 'class="viewer-layout"' in html
    assert 'class="viewer-left-col"' in html
    assert 'class="viewer-center-col"' in html
    assert 'class="viewer-right-col"' in html

    # Thumbnail strip & 5 folios
    assert 'class="thumbnail-strip"' in html
    assert 'thumb-ambedkar_speech_vol1_p0001' in html
    assert 'thumb-ambedkar_speech_vol1_p0005' in html

    # Pan/zoom toolbar controls
    assert 'id="btn-zoom-in"' in html
    assert 'id="btn-zoom-out"' in html
    assert 'id="btn-zoom-reset"' in html
    assert 'id="btn-fit-width"' in html
    assert 'id="btn-pan-toggle"' in html
    assert 'id="zoom-level-indicator"' in html

    # Canvas & overlay
    assert 'id="viewer-canvas-container"' in html
    assert 'id="viewer-transform-wrap"' in html
    assert 'id="viewer-image"' in html
    assert 'id="viewer-bbox-overlay"' in html

    # Metadata & transcript panel
    assert 'id="viewer-metadata-box"' in html
    assert 'id="viewer-transcript-text"' in html
    assert 'id="viewer-token-regions-list"' in html
    assert "Inspect Chain of Custody (6-Stage Provenance) 🔗" in html

    # Evidence badge & truthful degradation verbatim string
    assert "SOURCE EVIDENCE" in scripts
    assert "Region-level evidence unavailable for this record." in html
    assert "Region-level evidence unavailable for this record." in scripts


# -----------------------------------------------------------------------------
# 2. R5: Research Assistant Truthful Framing & Evidence Grounding
# -----------------------------------------------------------------------------

def test_research_assistant_truthful_framing_disclaimer_banner(client):
    """Verify prominent institutional Truthful Framing disclaimer banner in assistant workspace."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert "assistant-truthful-framing-banner" in html
    expected_banner_text = (
        "Archival Research Synthesis is grounded strictly in retrieved historical primary sources "
        "and does not claim infallible historical omniscience."
    )
    assert expected_banner_text in html


def test_research_assistant_preserved_invariants_and_refusal(client):
    """Verify assistant 3-column workspace, session history, citation tags, persistent evidence drawer, and refusal."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    scripts = get_scripts()

    # 3-column layout classes
    assert 'class="assistant-layout"' in html
    assert 'class="assistant-left-col"' in html
    assert 'class="assistant-center-col"' in html
    assert 'class="assistant-right-col"' in html

    # Left pane
    assert 'class="session-history-pane"' in html
    assert 'id="assistant-session-history"' in html
    assert 'id="assistant-citation-tags"' in html
    assert "#WritingsAndSpeeches" in html
    assert "#Constitution1950" in html

    # Center pane
    assert 'id="qa-input-assistant"' in html
    assert 'id="btn-submit-assistant-qa"' in html
    assert 'id="assistant-answer-stream"' in html

    # Right pane persistent evidence drawer
    assert 'class="evidence-drawer-pane"' in html
    assert "Persistent Evidence Drawer" in html
    assert "Citation Inspector" in html
    assert "Attribution Verification" in html
    assert 'id="assistant-citations-list"' in html

    # Principled algorithmic refusal card verbatim text
    refusal_verbatim = "Insufficient archival evidence found for a supported answer."
    assert refusal_verbatim in scripts
    assert refusal_verbatim in html


# -----------------------------------------------------------------------------
# 3. R7: Dedicated Touchscreen Kiosk & Smart Display Experience
# -----------------------------------------------------------------------------

def test_kiosk_five_discovery_categories_and_dual_preservation():
    """Verify the 5 R7 discovery categories and legacy asserted strings in Kiosk HTML."""
    kiosk_html = build_kiosk_html()

    # 5 R7 Discovery Categories
    assert "Start Exploring" in kiosk_html
    assert "Listen" in kiosk_html
    assert "Timeline" in kiosk_html
    assert "Search" in kiosk_html
    assert "Featured Documents" in kiosk_html

    # Legacy strings preserved via Dual-Preservation Pattern
    assert "Explore Heritage" in kiosk_html
    assert "Search" in kiosk_html
    assert "Timeline" in kiosk_html
    assert "Listen" in kiosk_html
    assert "Watch" in kiosk_html
    assert "Ask" in kiosk_html
    assert "Explore Manuscripts" in kiosk_html
    assert "Chronological Timeline" in kiosk_html


def test_kiosk_home_button_and_touch_target_constraints():
    """Verify prominent Home / Back touch control (>=48px) and touch target CSS variables."""
    kiosk_html = build_kiosk_html()

    # Home / Return to Main touch button
    assert 'id="btn-kiosk-home"' in kiosk_html
    assert 'class="btn-kiosk-touch"' in kiosk_html
    assert 'onclick="kioskNav(\'home\')"' in kiosk_html
    assert "🏠 Home / Return to Main" in kiosk_html

    # kioskNav function in scripts
    assert "function kioskNav(" in kiosk_html

    # Strict >= 48px touch target enforcement
    assert "--kiosk-touch-min: 48px;" in kiosk_html
    assert "min-height: 48px;" in kiosk_html
    assert "min-width: 48px;" in kiosk_html
    assert ".btn-kiosk-touch" in kiosk_html


def test_kiosk_smart_display_ambient_mode_preserved():
    """Verify 8s cycling Smart Display Ambient Mode and pause/resume logic are preserved."""
    kiosk_html = build_kiosk_html()

    assert "ambient-display-mode" in kiosk_html
    assert "btn-ambient-toggle" in kiosk_html
    assert "Smart Display Mode" in kiosk_html
    assert "ambient-progress-bar" in kiosk_html
    assert "DURATION_MS = 8000" in kiosk_html
    assert "onAmbientTouch" in kiosk_html
    assert "PAUSED (Touch to Resume)" in kiosk_html
    assert "Space" in kiosk_html

    # Authentic exhibits
    assert "Castes in India" in kiosk_html
    assert "Annihilation of Caste" in kiosk_html
    assert "Constituent Assembly Final Address" in kiosk_html


# -----------------------------------------------------------------------------
# 4. Advisory Fix: Flexible Institution Matching
# -----------------------------------------------------------------------------

def test_flexible_institution_filter_matching():
    """Verify scripts.py has flexible substring matching for institutions including PMML."""
    scripts = get_scripts()

    assert "item.institution" in scripts
    assert "primaryPart" in scripts or "split('/')" in scripts

    # Verify that Nehru Memorial Museum & Library / PMML matches catalog items
    catalog = get_catalog_items()
    pmml_filter = "Nehru Memorial Museum & Library / PMML"
    primary_part = pmml_filter.split("/")[0].strip().lower()

    matching_items = [
        item for item in catalog
        if primary_part in (item.get("institution") or "").lower()
    ]
    assert len(matching_items) >= 2
    for it in matching_items:
        assert "Nehru Memorial Museum & Library" in it["institution"]


# -----------------------------------------------------------------------------
# 5. Styling Verification
# -----------------------------------------------------------------------------

def test_styles_milestone3_css_rules():
    """Verify styles.py provides CSS rules for viewer prev/next controls and assistant framing banner."""
    css = get_styles()

    assert "#btn-viewer-prev-page" in css
    assert "#btn-viewer-next-page" in css
    assert ".assistant-truthful-framing-banner" in css
    assert ".banner-title" in css
