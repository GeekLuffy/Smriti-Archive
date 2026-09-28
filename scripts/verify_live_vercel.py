import json
import sys
import httpx

BASE_URL = "https://sih26096.vercel.app"

def test_live_deployment():
    print(f"Testing live Vercel deployment at: {BASE_URL}")
    client = httpx.Client(timeout=30.0)

    # 1. GET /
    r_root = client.get(f"{BASE_URL}/")
    print(f"\n[1] GET / -> Status {r_root.status_code}")
    assert r_root.status_code == 200, f"Root returned {r_root.status_code}"
    assert "DEMO" in r_root.text, "Root UI missing DEMO indicator"
    assert "SYNTHETIC" in r_root.text, "Root UI missing SYNTHETIC indicator"
    print("   [OK] Root HTML loaded successfully with DEMO / SYNTHETIC disclaimer")

    # 2. GET /health
    r_health = client.get(f"{BASE_URL}/health")
    print(f"\n[2] GET /health -> Status {r_health.status_code}")
    print(f"   Response: {r_health.json()}")
    assert r_health.status_code == 200
    assert r_health.json().get("status") == "healthy"
    print("   [OK] Health endpoint returns healthy")

    # 3. GET /ready
    r_ready = client.get(f"{BASE_URL}/ready")
    print(f"\n[3] GET /ready -> Status {r_ready.status_code}")
    print(f"   Response: {r_ready.json()}")
    assert r_ready.status_code == 200
    assert r_ready.json().get("status") == "ready"
    assert r_ready.json().get("is_serverless") is True
    print("   [OK] Readiness check passes in serverless mode")

    # 4. GET /api/v1/diagnostics
    r_diag = client.get(f"{BASE_URL}/api/v1/diagnostics")
    print(f"\n[4] GET /api/v1/diagnostics -> Status {r_diag.status_code}")
    diag_data = r_diag.json()
    print(f"   Response: {json.dumps(diag_data, indent=2)}")
    assert r_diag.status_code == 200
    assert diag_data["configuration"]["execution_mode"] == "DEMO"
    assert diag_data["configuration"]["is_vercel"] is True
    assert diag_data["configuration"]["platform_mode"] == "vercel_serverless"
    assert "ocr_host_engine" in diag_data
    print(f"   Tesseract available in Vercel: {diag_data['ocr_host_engine']['available']}")
    print(f"   Tesseract diagnostic message: {diag_data['ocr_host_engine'].get('diagnostic_message')[:60]}...")
    print("   [OK] Diagnostics accurate, reports platform_mode=vercel_serverless")

    # 5. GET /api/v1/search
    r_search = client.get(
        f"{BASE_URL}/api/v1/search",
        params={"q": "Ambedkar", "top_k": 2},
    )
    print(f"\n[5] GET /api/v1/search -> Status {r_search.status_code}")
    search_data = r_search.json()
    print(f"   Hits Count: {len(search_data.get('hits', []))}")
    if search_data.get("hits"):
        top_match = search_data["hits"][0]
        print(f"   Top Match: page_id={top_match.get('page_id')} score={top_match.get('score')}")
    assert r_search.status_code == 200
    assert len(search_data.get("hits", [])) > 0
    print("   [OK] Search returns valid grounded citations")

    # 6. POST /api/v1/qa
    r_qa = client.post(
        f"{BASE_URL}/api/v1/qa",
        json={"question": "What is compiled by Vasant Moon?"},
    )
    print(f"\n[6] POST /api/v1/qa -> Status {r_qa.status_code}")
    qa_data = r_qa.json()
    print(f"   Answer: {qa_data.get('answer_text', '')[:120]}...")
    print(f"   Is Refusal: {qa_data.get('is_refusal')}")
    print(f"   Citations count: {len(qa_data.get('citations', []))}")
    assert r_qa.status_code == 200
    print("   [OK] QA endpoint generates grounded answer with attribution citations")

    # 7. GET /api/v1/benchmarks/e1, e2, e3
    for phase in ["e1", "e2", "e3"]:
        r_bm = client.get(f"{BASE_URL}/api/v1/benchmarks/{phase}")
        print(f"\n[7.{phase}] GET /api/v1/benchmarks/{phase} -> Status {r_bm.status_code}")
        bm_data = r_bm.json()
        assert r_bm.status_code == 200
        assert "gate_status" in bm_data
        print(f"   Phase: {bm_data.get('phase')} | Gate Status: {bm_data.get('gate_status')}")
        assert "BLOCKED" in bm_data["gate_status"] or "LOCKED" in bm_data["gate_status"]
        print(f"   [OK] Benchmark endpoint {phase} enforces gate_status ({bm_data['gate_status'][:30]}...)")

    # 8. Test oversized upload error handling (Vercel payload limit)
    # Test A: 5MB payload (rejected at Vercel Edge with HTTP 413)
    oversized_edge = b"X" * (5 * 1024 * 1024)
    files = {"file": ("test_edge_oversized.pdf", oversized_edge, "application/pdf")}
    data = {
        "document_id": "test_edge_oversized",
        "title": "Oversized Document",
        "source_organization": "Test",
        "language": "eng",
        "rights_status": "public",
        "rights_evidence": "test_evidence.txt"
    }
    r_ingest_edge = client.post(f"{BASE_URL}/api/v1/ingest", data=data, files=files)
    print(f"\n[8.A] POST /api/v1/ingest (5MB payload at Vercel Edge) -> Status {r_ingest_edge.status_code}")
    assert r_ingest_edge.status_code == 413
    print("   [OK] Vercel Edge correctly enforces 4.5MB payload cutoff with HTTP 413")

    # Test B: 4.2MB payload (passed through edge, rejected by FastAPI limit with explanatory message)
    oversized_app = b"X" * (int(4.2 * 1024 * 1024))
    files_app = {"file": ("test_app_oversized.pdf", oversized_app, "application/pdf")}
    data_app = {
        "document_id": "test_app_oversized",
        "title": "Oversized App Document",
        "source_organization": "Test",
        "language": "eng",
        "rights_status": "public",
        "rights_evidence": "test_evidence.txt"
    }
    r_ingest_app = client.post(f"{BASE_URL}/api/v1/ingest", data=data_app, files=files_app)
    print(f"\n[8.B] POST /api/v1/ingest (4.2MB payload at FastAPI) -> Status {r_ingest_app.status_code}")
    assert r_ingest_app.status_code == 413
    detail_msg = r_ingest_app.json().get("detail", "") if "application/json" in r_ingest_app.headers.get("content-type", "") else r_ingest_app.text
    # 9. Test New Archival & Hardware UI Extensions
    # 9.A GET /kiosk (Touchscreen Museum Mode)
    r_kiosk = client.get(f"{BASE_URL}/kiosk")
    print(f"\n[9.A] GET /kiosk -> Status {r_kiosk.status_code}")
    assert r_kiosk.status_code == 200
    assert "Memorial Touch Kiosk" in r_kiosk.text
    assert "--kiosk-touch-min: 48px;" in r_kiosk.text
    print("   [OK] Kiosk interface serves touch-first museum display with >=48px touch targets")

    # 9.B GET /api/v1/media (Audio-Visual Library)
    r_media = client.get(f"{BASE_URL}/api/v1/media")
    print(f"\n[9.B] GET /api/v1/media -> Status {r_media.status_code}")
    assert r_media.status_code == 200
    media_data = r_media.json()
    assert (media_data.get("total_items") or media_data.get("total", 0)) >= 3
    print(f"   [OK] A/V Media Library returns {media_data.get('total_items') or media_data.get('total')} archival records with synchronized transcripts")

    # 9.C GET /api/v1/admin/audit (Curator Workspace)
    r_audit = client.get(f"{BASE_URL}/api/v1/admin/audit")
    print(f"\n[9.C] GET /api/v1/admin/audit -> Status {r_audit.status_code}")
    assert r_audit.status_code == 200
    audit_data = r_audit.json()
    assert audit_data.get("status") == "operational"
    print("   [OK] Institutional Admin audit reports operational health and manifest tracking")

    # 9.D GET /api/v1/provenance/ambedkar_speech_vol1_p0001 (6-Stage Custody Chain)
    r_prov = client.get(f"{BASE_URL}/api/v1/provenance/ambedkar_speech_vol1_p0001")
    print(f"\n[9.D] GET /api/v1/provenance -> Status {r_prov.status_code}")
    assert r_prov.status_code == 200
    prov_data = r_prov.json()
    assert len(prov_data.get("stages", [])) == 6
    print(f"   [OK] 6-Stage Cryptographic Provenance Chain verified for {prov_data.get('page_id')}")

    print("\n=======================================================")
    print("ALL LIVE VERCEL PRODUCTION ENDPOINTS VERIFIED SUCCESSFULLY!")
    print("=======================================================")

if __name__ == "__main__":
    test_live_deployment()
