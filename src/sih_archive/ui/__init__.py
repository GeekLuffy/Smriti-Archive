"""
SIH26096 Archival User Interface Package.

Exports catalog fixtures, design tokens, styling, scripts, and page builders.
"""

from sih_archive.ui.fixtures import (
    CATALOG_ITEMS,
    CURATED_COLLECTIONS,
    DISCOVERY_PATHWAYS,
    MEDIA_RECORDS,
    TIMELINE_EVENTS,
    get_catalog_item,
    get_catalog_items,
    get_curated_collections,
    get_discovery_pathways,
    get_media_record,
    get_media_records,
    get_timeline_event,
    get_timeline_events,
)
from sih_archive.ui.page_builder import build_kiosk_html, build_portal_html
from sih_archive.ui.scripts import get_scripts
from sih_archive.ui.styles import THEME_TOKENS, get_styles

__all__ = [
    "DISCOVERY_PATHWAYS",
    "CURATED_COLLECTIONS",
    "CATALOG_ITEMS",
    "TIMELINE_EVENTS",
    "MEDIA_RECORDS",
    "get_discovery_pathways",
    "get_curated_collections",
    "get_catalog_items",
    "get_timeline_events",
    "get_media_records",
    "get_catalog_item",
    "get_timeline_event",
    "get_media_record",
    "THEME_TOKENS",
    "get_styles",
    "get_scripts",
    "build_portal_html",
    "build_kiosk_html",
]
