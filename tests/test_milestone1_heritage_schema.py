"""
Automated Verification Suite for Milestone 1: 19-Field Heritage Record Schema,
24 Authentic Historical Records Corpus, Design Tokens, and Catalog API Endpoints.

Verifies:
1. Pydantic HeritageRecord and ProvenanceMetadata schema models in sih_archive.schemas.heritage.
2. Complete 19-field + 9 auxiliary backward-compatibility fields across all 24 catalog records in fixtures.py.
3. Full coverage across all 6 historical collections.
4. Lookup by both primary 'id' and legacy 'document_id' in get_catalog_item.
5. GET /api/v1/catalog list endpoint with query filtering and dual array serialization (records, items).
6. GET /api/v1/catalog/{item_id} endpoint with 404 error handling.
7. GET /api/v1/admin/audit catalog health and 19-field compliance metrics.
8. Terracotta color token integration in styles.py.
9. Non-blurry museum-grade opaque scrim for #provenance-modal in page_builder.py.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

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
)
from sih_archive.ui.page_builder import build_portal_html
from sih_archive.ui.styles import THEME_TOKENS, get_styles


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient with initialized lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


# -----------------------------------------------------------------------------
# 1. Schema Unit & Validation Tests
# -----------------------------------------------------------------------------

def test_provenance_metadata_model():
    """Verify ProvenanceMetadata instantiates and validates required custodial provenance fields."""
    prov_data = {
        "custodial_history": "Transferred directly from Constituent Assembly Secretariat to NAI.",
        "source_organization": "National Archives of India",
        "source_url": "https://nationalarchives.nic.in",
        "accession_number": "NAI-CAD-1948-001",
        "custody_chain": [
            "Constituent Assembly Secretariat (1948)",
            "Parliament House Archives (1950)",
            "National Archives of India (1975)",
        ],
        "legal_basis": "Statutory archival preservation clearance under Public Records Act 1993.",
        "checksum_sha256": "4a7d1ed414474e4033ac29ccb8653d9b139045b85e05a8f4c281df6f88d74542",
    }
    prov = ProvenanceMetadata(**prov_data)
    assert prov.source_organization == "National Archives of India"
    assert len(prov.custody_chain) == 3
    assert prov.checksum_sha256 is not None


def test_heritage_record_schema_valid():
    """Verify HeritageRecord successfully instantiates with all 19 standard fields and validates aliases."""
    rec_data = {
        "id": "cat_test_record_01",
        "title": "Historical Proclamation of Rights",
        "subtitle": "A Declaration for Social Justice",
        "collection": "Writings & Speeches",
        "date": "1948-02-21",
        "language": "eng",
        "document_type": "Debate Proceeding",
        "institution": "National Archives of India, New Delhi",
        "source": "Government of India Official Records",
        "description": "Foundational archival text establishing democratic social rights.",
        "thumbnail": "/api/v1/pages/test_p0001/image",
        "page_images": ["/api/v1/pages/test_p0001/image"],
        "transcript": "Full archival transcript of the proclamation.",
        "audio": None,
        "video": None,
        "rights": "public",
        "provenance": {
            "custodial_history": "Official preservation transfer.",
            "source_organization": "National Archives of India",
            "legal_basis": "Public Records Act 1993 Section 5.",
        },
        "related_items": ["cat_ambedkar_vol1"],
        "timeline_event": "evt_1948_draft_constitution",
    }

    record = HeritageRecord(**rec_data)
    assert record.id == "cat_test_record_01"
    assert record.title == "Historical Proclamation of Rights"
    assert record.collection == "Writings & Speeches"
    assert record.rights == "public"

    # Test backward compatibility auto-populated accessors
    assert record.document_id == "test_record_01"
    assert record.author == "Dr. B. R. Ambedkar"
    assert record.summary == "Foundational archival text establishing democratic social rights."
    assert record.material_type == "Debate Proceeding"
    assert record.preview_page_id == "ambedkar_speech_vol1_p0001"
    assert record.has_ocr is True
    assert record.has_image is True
    assert record.rights_evidence == "Public Records Act 1993 Section 5."


def test_heritage_record_schema_missing_required_fields():
    """Verify HeritageRecord rejects dictionaries lacking required fields."""
    incomplete_data = {
        "id": "cat_incomplete_01",
        "title": "Incomplete Record",
        # Missing collection, date, language, document_type, institution, source, description, etc.
    }
    with pytest.raises(ValidationError):
        HeritageRecord(**incomplete_data)


# -----------------------------------------------------------------------------
# 2. Authentic 24-Record Corpus & Fixtures Invariants
# -----------------------------------------------------------------------------

def test_catalog_corpus_size_and_pydantic_validation():
    """Verify CATALOG_ITEMS contains exactly 24 records, each valid per HeritageRecord."""
    items = get_catalog_items()
    assert len(items) == 24
    assert len(CATALOG_ITEMS) == 24

    for item in items:
        # Pydantic 19-field validation
        validated = HeritageRecord(**item)
        assert validated.id == item["id"]


def test_catalog_corpus_six_collections_coverage():
    """Verify all 6 canonical collections are populated in the authentic corpus."""
    items = get_catalog_items()
    collections_in_corpus = {item["collection"] for item in items}
    assert collections_in_corpus == ALLOWED_COLLECTIONS
    assert len(collections_in_corpus) == 6

    # Verify at least 3 records per collection for balanced archival depth
    for coll in ALLOWED_COLLECTIONS:
        coll_records = [i for i in items if i["collection"] == coll]
        assert len(coll_records) >= 3, f"Collection '{coll}' has fewer than 3 records ({len(coll_records)})"


def test_catalog_corpus_backward_compatibility_keys():
    """Verify each dictionary in CATALOG_ITEMS retains all 9 backward-compatibility keys."""
    expected_legacy_keys = {
        "document_id",
        "author",
        "summary",
        "material_type",
        "preview_page_id",
        "has_ocr",
        "has_image",
        "page_count",
        "rights_evidence",
    }

    items = get_catalog_items()
    for item in items:
        for key in expected_legacy_keys:
            assert key in item, f"Record '{item.get('id')}' missing legacy key '{key}'"


def test_catalog_corpus_all_19_standard_fields():
    """Verify each dictionary in CATALOG_ITEMS contains all 19 standard fields."""
    expected_standard_fields = {
        "id",
        "title",
        "subtitle",
        "collection",
        "date",
        "language",
        "document_type",
        "institution",
        "source",
        "description",
        "thumbnail",
        "page_images",
        "transcript",
        "audio",
        "video",
        "rights",
        "provenance",
        "related_items",
        "timeline_event",
    }

    items = get_catalog_items()
    for item in items:
        for field in expected_standard_fields:
            assert field in item, f"Record '{item.get('id')}' missing standard field '{field}'"


def test_get_catalog_item_dual_lookup():
    """Verify get_catalog_item retrieves by both primary 'id' and legacy 'document_id'."""
    # Lookup by primary id
    item_by_id = get_catalog_item("cat_cad_draft_1948")
    assert item_by_id is not None
    assert item_by_id["title"] == "Constituent Assembly Debates: Motion Introducing Draft Constitution"

    # Lookup by legacy document_id
    item_by_doc_id = get_catalog_item("ambedkar_speech_vol1")
    assert item_by_doc_id is not None
    assert item_by_doc_id["id"] == "cat_ambedkar_vol1"
    assert item_by_doc_id["document_id"] == "ambedkar_speech_vol1"

    # Non-existent ID returns None
    assert get_catalog_item("non_existent_record_xyz") is None


# -----------------------------------------------------------------------------
# 3. Design Tokens & Visual Invariant Tests
# -----------------------------------------------------------------------------

def test_terracotta_design_token_present():
    """Verify terracotta token is registered in THEME_TOKENS and exported in CSS root."""
    colors = THEME_TOKENS["colors"]
    assert "terracotta" in colors
    assert colors["terracotta"] == "#9a3412"

    css = get_styles()
    assert "--accent-terracotta: #9a3412;" in css


def test_glassmorphism_scrim_fix_in_page_builder():
    """Verify #provenance-modal uses museum-grade opaque scrim without blur filter."""
    html = build_portal_html()
    assert 'id="provenance-modal"' in html
    # Check for absence of backdrop-filter in provenance-modal rule
    assert "backdrop-filter: blur(3px);" not in html
    # Check for presence of the 85% opacity slate scrim
    assert "background: rgba(15, 23, 42, 0.85);" in html


# -----------------------------------------------------------------------------
# 4. Catalog & Audit API Endpoints Tests
# -----------------------------------------------------------------------------

def test_api_catalog_list_endpoint(client):
    """Verify GET /api/v1/catalog returns all 24 records and matches schema contract."""
    response = client.get("/api/v1/catalog")
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 24
    assert data["total_items"] == 24
    assert len(data["records"]) == 24
    assert len(data["items"]) == 24
    assert data["schema_version"] == "19-field-r6"


def test_api_catalog_list_filtering(client):
    """Verify GET /api/v1/catalog filters by collection, language, document_type, institution, and limit."""
    # 1. Collection filter
    res_coll = client.get("/api/v1/catalog?collection=Constitutional Debates")
    assert res_coll.status_code == 200
    records_coll = res_coll.json()["records"]
    assert len(records_coll) == 5
    for r in records_coll:
        assert r["collection"] == "Constitutional Debates"

    # 2. Language filter
    res_lang = client.get("/api/v1/catalog?language=mar")
    assert res_lang.status_code == 200
    records_lang = res_lang.json()["records"]
    assert len(records_lang) >= 2
    for r in records_lang:
        assert r["language"] == "mar"

    # 3. Document type filter (partial / substring match)
    res_doctype = client.get("/api/v1/catalog?document_type=Debate")
    assert res_doctype.status_code == 200
    records_doctype = res_doctype.json()["records"]
    assert len(records_doctype) >= 1
    for r in records_doctype:
        assert "debate" in r["document_type"].lower() or "debate" in r.get("material_type", "").lower()

    # 4. Institution filter
    res_inst = client.get("/api/v1/catalog?institution=National Archives of India")
    assert res_inst.status_code == 200
    records_inst = res_inst.json()["records"]
    assert len(records_inst) >= 1
    for r in records_inst:
        assert "National Archives of India" in r["institution"]

    # 5. Limit filter
    res_limit = client.get("/api/v1/catalog?limit=5")
    assert res_limit.status_code == 200
    records_limit = res_limit.json()["records"]
    assert len(records_limit) == 5


def test_api_catalog_detail_endpoint(client):
    """Verify GET /api/v1/catalog/{item_id} retrieves item or returns 404."""
    # Valid by id
    res_valid_id = client.get("/api/v1/catalog/cat_cad_draft_1948")
    assert res_valid_id.status_code == 200
    item = res_valid_id.json()
    assert item["id"] == "cat_cad_draft_1948"
    assert item["date"] == "1948-11-04"

    # Valid by document_id
    res_valid_doc = client.get("/api/v1/catalog/ambedkar_speech_vol1")
    assert res_valid_doc.status_code == 200
    item_doc = res_valid_doc.json()
    assert item_doc["id"] == "cat_ambedkar_vol1"
    assert item_doc["document_id"] == "ambedkar_speech_vol1"

    # Invalid ID 404
    res_404 = client.get("/api/v1/catalog/unknown_nonexistent_id")
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()


def test_api_admin_audit_catalog_metrics(client):
    """Verify GET /api/v1/admin/audit reports catalog preservation counts and 19-field compliance."""
    response = client.get("/api/v1/admin/audit")
    assert response.status_code == 200
    data = response.json()

    assert data["catalog_records_count"] == 24
    assert data["schema_19_field_compliance"] is True
    assert "catalog_preservation" in data
    pres = data["catalog_preservation"]
    assert pres["catalog_records_count"] == 24
    assert pres["schema_19_field_compliance"] is True
    assert pres["collections_covered"] == 6
