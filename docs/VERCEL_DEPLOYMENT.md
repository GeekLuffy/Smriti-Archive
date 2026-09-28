# SIH26096 — Vercel Serverless Deployment Guide

**System:** Digital Heritage Archive for Memorials, Manuscripts & Ambedkar: AI-Powered Institutional Archive and Audio-Visual Knowledge Platform  
**Target Architecture:** Vercel Serverless (Public Presentation / Demonstration Layer) coexisting with Northflank / On-Premises Compute  
**Runtime:** Python 3.11 Serverless Function (`api/index.py` with `vercel.json` rewrite)  
**Execution Mode:** `DEMO` (by default on Vercel)  
**Research Integrity Level:** Strict separation between `DEMO / SYNTHETIC DATA` and `VALIDATED EMPIRICAL HISTORICAL RESULTS`  

---

## 1. Executive Deployment Topology (Vercel + Northflank Coexistence)

The SIH26096 architecture intentionally decouples the public demonstration and web inquiry layer from heavy computational pipelines:

```
+-------------------------------------------------------------------------------------------------+
|                                    MULTI-TIER CLOUD ARCHITECTURE                                |
+-------------------------------------------------------------------------------------------------+

                      [ Public Users / SIH Evaluators / Researchers ]
                                             |
                                             v
               +-----------------------------------------------------------+
               |                TIER 1: VERCEL SERVERLESS                  |
               |             (Public Web & Demonstration Layer)            |
               |  - Global edge CDN routing (vercel.json)                  |
               |  - Lightweight FastAPI serverless function (api/index.py) |
               |  - Responsive HTML Demo UI (GET /)                        |
               |  - Interactive Search (/api/v1/search)                    |
               |  - Evidence-Grounded QA (/api/v1/qa)                      |
               |  - Operational Diagnostics (/api/v1/diagnostics)          |
               |  - Mode: DEMO / SYNTHETIC DATA (Prominently Disclaimed)   |
               +-----------------------------+-----------------------------+
                                             |
                     API Coordination /      | Direct-to-Storage
                     Read-Only Retrieval     | Pre-Signed Uploads
                                             |
                                             v
               +-----------------------------------------------------------+
               |          TIER 2: PERSISTENT INSTITUTIONAL STORAGE         |
               |     (S3-Compatible Object Store / Northflank Volume)      |
               |  - Archival Raw PDFs & High-Res Scans (/data/raw/)        |
               |  - Intellectual Property Rights Manifests (/manifests/)  |
               |  - Independent Paleographic Ground Truth (/ground_truth/) |
               |  - Machine-Readable Benchmark Outputs (/results/)         |
               |  - Embedding Model Weights (/cache/models/)               |
               +-----------------------------+-----------------------------+
                                             ^
                                             | Reads Scans / Writes OCR
                                             |
               +-----------------------------+-----------------------------+
               |             TIER 3: NORTHFLANK / ON-PREMISES              |
               |          (Heavy AI & Empirical Benchmark Workers)         |
               |  - Debian Docker container with system Tesseract v5       |
               |  - Language models: eng, hin, mar                         |
               |  - 300 DPI high-resolution PyMuPDF rasterization          |
               |  - Preprocessing variation pipelines (CLAHE, Otsu, Deskew)|
               |  - Full batch empirical benchmark evaluation              |
               +-----------------------------------------------------------+
```

---

## 2. Vercel Setup & Project Configuration

### Step 1: Push Repository to GitHub
Ensure your repository is pushed to GitHub (`GeekLuffy/SIH26096`).

### Step 2: Import into Vercel
1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Select GitHub repository `GeekLuffy/SIH26096`.
4. Framework Preset: Leave as **Other** (Vercel automatically detects `vercel.json` and `api/index.py`).
5. Root Directory: `./` (project root).

### Step 3: Project Configuration Files
The repository includes the necessary configuration files for Vercel:

1. [`vercel.json`](file:///F:/Projects/SIH26096/vercel.json):
   ```json
   {
     "version": 2,
     "rewrites": [
       {
         "source": "/(.*)",
         "destination": "/api/index.py"
       }
     ]
   }
   ```
2. [`api/index.py`](file:///F:/Projects/SIH26096/api/index.py):
   Serverless entrypoint that configures the Python search path, sets serverless defaults (`EXECUTION_MODE=DEMO`), and exposes the ASGI `app` instance.

---

## 3. Environment Variables Configuration

Configure these in the **Settings -> Environment Variables** tab on the Vercel dashboard:

| Variable | Recommended Vercel Value | Description |
| :--- | :--- | :--- |
| `EXECUTION_MODE` | `DEMO` | Sets presentation mode displaying verified synthetic previews with clear banners. |
| `APP_ENV` | `vercel` | Declares runtime environment for read-only filesystem handling. |
| `APP_DEBUG` | `false` | Must remain `false` in production. |
| `ARCHIVE_DATA_DIR` | `/tmp/data` or External Mount | Directs writable data to `/tmp` (or external storage). |
| `GROUND_TRUTH_DIR` | `./data/ground_truth` | Location of ground truth reference transcripts. |
| `RESULTS_DIR` | `./results` | Location of machine-readable benchmark JSON files. |
| `MAX_UPLOAD_SIZE_BYTES` | `4194304` (4MB) | Enforces 4MB ceiling to stay within Vercel's 4.5MB payload limit. |
| `OCR_DEVICE` | `cpu` | Device selection (Vercel serverless runs on CPU). |
| `CORS_ORIGINS` | `*` | Allowed CORS origins for web client embedding. |

---

## 4. Storage Architecture & Platform Constraints

### Read-Only Filesystem in Vercel Serverless
- In Vercel Serverless Functions, the deployed application directory (`/var/task`) is strictly **read-only**.
- Only the `/tmp` directory is writable (up to 512MB ephemeral disk).
- **Rule:** The Vercel function filesystem must **never** be treated as authoritative archival storage.
- The `readiness_check` (`/ready`) detects Vercel serverless execution (`is_serverless=True`) and confirms that bundled static reference corpora exist to serve search and QA queries without failing on read-only disk checks.

### Large-File Ingestion Architecture
- **Vercel Payload Ceiling:** Vercel functions reject request bodies exceeding **4.5 MB** at the edge before the function executes.
- **Handling Archival Volumes:** Multi-page high-resolution archival scans often measure 20MB–500MB.
- **Architecture Solution:**
  1. The public Vercel API is designed for queries, metadata lookup, and demo exploration.
  2. Large archival document intake should be directed to Northflank container endpoints or use pre-signed URLs directly to S3-compatible cloud object storage.
  3. If an upload through `/api/v1/ingest` on Vercel exceeds 4MB, the API returns an informative `HTTP 413 Content Too Large` explaining the Vercel serverless ceiling and recommending direct-to-storage intake.

---

## 5. DEMO Mode on Vercel

On Vercel, the application defaults to `EXECUTION_MODE=DEMO`:
- **UI Banner:** Every page of the web UI displays:
  > `⚠️ DEMO / SYNTHETIC DATA — NOT VALIDATED EMPIRICAL HISTORICAL RESULTS`
- **API Responses:** All `/api/v1/search` and `/api/v1/qa` responses include:
  ```json
  {
    "execution_mode": "DEMO_SYNTHETIC",
    "disclaimer": "DEMO / SYNTHETIC DATA — NOT VALIDATED EMPIRICAL HISTORICAL RESULTS"
  }
  ```
- **Integrity Notice:** The diagnostics endpoint explicitly declares that rights/provenance metadata validation is `MEASURED`, while substantive legal authorization for a specific corpus is `NOT ESTABLISHED BY SOFTWARE TEST` and requires institutional clearance.

---

## 6. OCR Limitations in Serverless Functions

- **Absence of Host Tesseract:** Vercel serverless containers do not include system packages like `tesseract-ocr`.
- **Truthful Reporting:** The application does **not** assume Tesseract is present and never fabricates mock OCR text as real output.
- When `/api/v1/diagnostics` is queried on Vercel, it truthfully reports:
  ```json
  {
    "ocr_host_engine": {
      "name": "Tesseract OCR",
      "available": false,
      "diagnostic_message": "Tesseract OCR binary not found...",
      "configured_device": "cpu",
      "available_languages": []
    }
  }
  ```
- Full OCR execution on authentic historical scans remains assigned to Northflank containers or on-premises GPU/CPU workstations where Tesseract v5 is installed.

---

## 7. How Vercel and Northflank Coexist

| Feature / Responsibility | Vercel Deployment | Northflank Deployment |
| :--- | :--- | :--- |
| **Primary Role** | Public Web, Demonstration, Evaluator UI | Institutional Archive Service & Heavy Compute |
| **Container Runtime** | AWS Lambda / Serverless (Python 3.11) | Docker (Debian 12 / Python 3.11-slim) |
| **Tesseract OCR Binary** | Not installed (truthfully reported) | Installed (`eng`, `hin`, `mar`) |
| **Max Payload Size** | 4.5 MB | 50 MB+ (configurable) |
| **Persistent Storage** | Ephemeral `/tmp` (Read-only app root) | Mounted Persistent SSD Volumes (`/app/data`) |
| **Process Lifecycle** | Stateless (spin-up on demand) | Persistent daemon with background workers |
| **SIH 2026 Target** | Fast, globally accessible judge demonstration | Archival preservation, ingestion, and benchmarking |

---

## 8. Verification & Local Testing

To test the Vercel entrypoint locally prior to deployment:
```bash
# Verify import and route registration
python -c "from api.index import app; print('Vercel entrypoint ready:', app.title)"

# Run automated Vercel deployment test suite
python -m pytest tests/test_vercel_deployment.py -v
```

---

## 9. VERIFIED LIVE DEPLOYMENT

The live production deployment on Vercel has been fully executed and empirically verified:

| Property | Verified Production Value |
| :--- | :--- |
| **Vercel Project URL** | [https://vercel.com/luffy-projects/sih26096](https://vercel.com/luffy-projects/sih26096) |
| **Production Aliased URL** | [https://sih26096.vercel.app](https://sih26096.vercel.app) |
| **Direct Deployment URL** | [https://sih26096-of1b4luwk-luffy-projects.vercel.app](https://sih26096-of1b4luwk-luffy-projects.vercel.app) |
| **Deployment ID** | `dpl_8rGVAS6bQTCYLFCc68vsjdJuQ5zQ` |
| **Deployment Status** | `READY` (HTTP 200) |
| **Runtime & Region** | Python 3.12.14 Serverless (`uv 0.10.11`) on `iad1` (Washington, D.C., USA) |
| **Execution Mode** | `DEMO` (`platform_mode: vercel_serverless`) |
| **OCR Host Engine** | Truthfully reported as `available: false` (Tesseract binary absent in Vercel runtime) |
| **Portal UI (`GET /`)** | Museum-grade Heritage Portal with hero section, 6 discovery cards, and research navigation |
| **Touch Kiosk (`GET /kiosk`)** | Physical museum installation mode with large touch targets (min 48px) and ambient display |
| **Health Probe (`GET /health`)** | `{"status": "healthy", "service": "sih26096-archive", "execution_mode": "DEMO"}` (HTTP 200) |
| **Readiness Probe (`GET /ready`)** | `{"status": "ready", "storage_ready": true, "is_serverless": true, "indexed_documents_count": 1}` (HTTP 200) |
| **Search API (`GET /api/v1/search`)** | Query `Ambedkar` returned 1 hit (`ambedkar_speech_vol1_p0001`, score: 0.0328) |
| **QA API (`POST /api/v1/qa`)** | Grounded answer with citation: `"Compiled by Vasant Moon." [Source: ambedkar_speech_vol1, Page: p0001]` |
| **Provenance Chain (`GET /api/v1/provenance/{id}`)** | 6-stage cryptographic custody verification (`Object -> Digital -> Page -> OCR -> Retrieval -> Answer`) |
| **A/V Media Catalog (`GET /api/v1/media`)** | 3 historical recordings with synchronized time-coded transcripts |
| **Curator Audit (`GET /api/v1/admin/audit`)** | Institutional operational status and manifest integrity reporting |
| **Benchmark Gating (`GET /api/v1/benchmarks/{p}`)** | `e1`: `BLOCKED_ON_HOST_OCR_BINARY`; `e2` & `e3`: `LOCKED_PREVIEW` |
| **Oversized Upload Safeguards** | 5MB edge payload rejected at Vercel Edge (HTTP 413); 4.2MB rejected by FastAPI limit with informative 4.5MB serverless error message |

