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
