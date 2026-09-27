"""
Production FastAPI Application for SIH26096 Archival System (Northflank Ready).

Serves:
- Operational health, readiness, and diagnostics endpoints
- Document intake and rights manifest management
- Resilient retrieval search engine (BM25, N-gram, Dense, Hybrid)
- Evidence-grounded QA with token-level bounding-box visual attribution
- Interactive DEMO interface with explicit research integrity disclaimers
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import shutil
import sys
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from sih_archive.attribution.evaluator import AttributionEvaluator
from sih_archive.attribution.pipeline import EvidenceGroundedAnswerPipeline
from sih_archive.config import ArchiveConfig, get_config
from sih_archive.ingestion.protocol import (
    audit_intake,
    check_rights_hygiene,
    create_manifest,
    discover_manifests,
    save_manifest,
    validate_manifest,
)
from sih_archive.ocr.tesseract import TesseractAdapter
from sih_archive.retrieval.base import RetrievalEngine, SearchResult
from sih_archive.retrieval.bm25 import BM25RetrievalEngine
from sih_archive.retrieval.dense import DenseRetrievalEngine, MockEmbeddingModel
from sih_archive.retrieval.hybrid import HybridRetrievalEngine
from sih_archive.retrieval.ngram import CharacterNGramRetrievalEngine
from sih_archive.schemas.manifest import DocumentManifest, RightsStatus
from sih_archive.schemas.ocr import OCROutput, ProcessingMetadata, TokenRegion

# Structured Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sih_archive.api")

# Global in-memory retrieval engines and pipeline
_engines: Dict[str, RetrievalEngine] = {}
_qa_pipeline: Optional[EvidenceGroundedAnswerPipeline] = None
_indexed_documents: List[OCROutput] = []

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}


def load_indexed_corpus(config: ArchiveConfig) -> List[OCROutput]:
    """Loads all OCR output documents available in the configured outputs or sample directory."""
    ocr_dir = config.outputs_dir / "ocr"
    docs: List[OCROutput] = []
    if ocr_dir.is_dir():
        for p in sorted(ocr_dir.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "regions" in data and "text" in data and "page_id" in data:
                    docs.append(OCROutput.model_validate(data))
            except Exception as e:
                logger.debug(f"Skipping non-OCR json {p}: {e}")

    # Fallback to standard synthetic preview sample if outputs/ocr has no valid pages
    if not docs:
        sample_doc = OCROutput(
            document_id="ambedkar_speech_vol1",
            page_id="ambedkar_speech_vol1_p0001",
            language="eng",
            script="Latn",
            engine="mock_synthetic",
            image_path="data/processed/pages/ambedkar_speech_vol1_p0001.png",
            processing=ProcessingMetadata(dpi=300, execution_duration_ms=10.0),
            text="DR. BABASAHEB AMBEDKAR WRITINGS AND SPEECHES VOL. 1. Compiled by Vasant Moon. Published by Education Department, Government of Maharashtra.",
            regions=[
                TokenRegion(text="DR.", bbox=[50, 100, 40, 20], confidence=99.0),
                TokenRegion(text="BABASAHEB", bbox=[95, 100, 120, 20], confidence=98.5),
                TokenRegion(text="AMBEDKAR", bbox=[220, 100, 110, 20], confidence=99.0),
                TokenRegion(text="WRITINGS", bbox=[50, 130, 90, 20], confidence=97.0),
                TokenRegion(text="Compiled", bbox=[50, 180, 80, 18], confidence=96.0),
                TokenRegion(text="by", bbox=[135, 180, 25, 18], confidence=95.0),
                TokenRegion(text="Vasant", bbox=[165, 180, 70, 18], confidence=98.0),
                TokenRegion(text="Moon", bbox=[240, 180, 50, 18], confidence=98.0),
                TokenRegion(text="Education", bbox=[50, 220, 90, 18], confidence=96.5),
                TokenRegion(text="Department", bbox=[145, 220, 110, 18], confidence=97.0),
            ],
        )
        docs.append(sample_doc)
    return docs


def initialize_engines(config: ArchiveConfig) -> None:
    """Instantiates retrieval engines and citation QA pipeline."""
    global _engines, _qa_pipeline, _indexed_documents
    _indexed_documents = load_indexed_corpus(config)

    bm25 = BM25RetrievalEngine()
    ngram = CharacterNGramRetrievalEngine(n=3)
    dense = DenseRetrievalEngine(embedding_model=MockEmbeddingModel(dim=32))
    hybrid = HybridRetrievalEngine(lexical_engine=bm25, dense_engine=dense, rrf_k=60)

    for eng in (bm25, ngram, dense, hybrid):
        eng.index_documents(_indexed_documents)

    _engines = {
        "bm25": bm25,
        "ngram": ngram,
        "dense": dense,
        "hybrid": hybrid,
    }

    _qa_pipeline = EvidenceGroundedAnswerPipeline(
        retrieval_engine=bm25,
        min_relevance_score=0.01,
        min_support_similarity=50.0,
    )
    _qa_pipeline.register_documents(_indexed_documents)
    logger.info(f"Initialized retrieval & QA engines with {len(_indexed_documents)} documents.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown management."""
    config = get_config()
    logger.info(f"Starting SIH26096 Archival System in mode '{config.execution_mode}' on port {config.port}...")
    config.ensure_directories()
    initialize_engines(config)
    yield
    logger.info("Gracefully shutting down SIH26096 Archival System...")


app = FastAPI(
    title="SIH26096 Digital Heritage Archive & Audio-Visual Knowledge Platform",
    description="Research-grade institutional archive with verifiable provenance, resilient OCR retrieval, and visual attribution.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
_config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Operational & Health Endpoints (Northflank Liveness/Readiness)
# ---------------------------------------------------------

@app.get("/health", tags=["Health & Observability"])
async def health_check() -> Dict[str, Any]:
    """Liveness probe confirming the server is running and responsive."""
    return {
        "status": "healthy",
        "service": "sih26096-archive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_mode": get_config().execution_mode,
    }


@app.get("/ready", tags=["Health & Observability"])
async def readiness_check() -> JSONResponse:
    """Readiness probe checking storage availability and retrieval engine initialization."""
    config = get_config()
    storage_status = config.get_storage_status()
    all_writable = all(s["writable"] for s in storage_status.values())
    all_exist = all(s["exists"] for s in storage_status.values())
    engines_ready = len(_engines) > 0 and _qa_pipeline is not None

    # In serverless environments (e.g. Vercel), static bundled demo data is read-only.
    # The function is ready to serve search and QA if directories exist and engines are ready.
    is_serverless = config.is_vercel or config.app_env in ("vercel", "serverless")
    storage_ready = all_exist if is_serverless else all_writable

    if not storage_ready or not engines_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "storage_ready": storage_ready,
                "storage_writable": all_writable,
                "is_serverless": is_serverless,
                "engines_ready": engines_ready,
                "storage_status": storage_status,
            },
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "storage_ready": True,
            "storage_writable": all_writable,
            "is_serverless": is_serverless,
            "engines_ready": True,
            "indexed_documents_count": len(_indexed_documents),
        },
    )


@app.get("/api/v1/diagnostics", tags=["Health & Observability"])
async def system_diagnostics() -> Dict[str, Any]:
    """Returns safe runtime diagnostics, OCR host binary state, and experiment gate statuses."""
    config = get_config()
    tess_adapter = TesseractAdapter()
    tess_available, tess_msg = tess_adapter.is_available()

    return {
        "service": "SIH26096 Archival System",
        "python_version": sys.version.split()[0],
        "configuration": config.get_safe_diagnostics(),
        "storage": config.get_storage_status(),
        "ocr_host_engine": {
            "name": "Tesseract OCR",
            "available": tess_available,
            "diagnostic_message": tess_msg,
            "configured_device": config.ocr_device,
            "available_languages": tess_adapter.get_available_languages() if tess_available else [],
        },
        "research_gates": {
            "E0_corpus_rights": "PASS (Intake & Provenance Metadata Validation: MEASURED; Legal authorization for specific corpus: NOT ESTABLISHED BY SOFTWARE TEST)",
            "E1_ocr_benchmark": "BLOCKED_ON_HOST_OCR_BINARY" if not tess_available else "READY",
            "E2_retrieval_benchmark": "LOCKED (Gated on empirical E1 completion)",
            "E3_attribution_benchmark": "LOCKED (Gated on empirical E1/E2 validation)",
            "E4_multilingual": "READY (Gated)",
            "E5_hardware": "READY (Gated)",
        },
        "research_integrity_notice": (
            "Rights and provenance metadata validation is MEASURED. Substantive legal authorization "
            "for a specific archival corpus is NOT ESTABLISHED BY SOFTWARE TEST and requires custodial "
            "institutional clearance. All preview figures on vector PDFs are synthetic demos. Real historical "
            "OCR accuracy cannot be claimed without physical scans and host OCR execution."
        ),
    }


# ---------------------------------------------------------
# Corpus & Manifest Management
# ---------------------------------------------------------

@app.get("/api/v1/manifests", tags=["Corpus & Intake"])
async def list_manifests() -> Dict[str, Any]:
    """Lists all registered archival document manifests with rights status and provenance."""
    config = get_config()
    manifests = discover_manifests(config.manifests_dir)
    return {
        "total_manifests": len(manifests),
        "manifests": [m.model_dump() for m in manifests],
    }


@app.post("/api/v1/ingest", tags=["Corpus & Intake"])
async def ingest_document(
    file: UploadFile = File(...),
    document_id: str = Form(...),
    title: str = Form(...),
    source_organization: str = Form(...),
    source_url: Optional[str] = Form(None),
    language: str = Form("eng"),
    script: Optional[str] = Form(None),
    rights_status: str = Form("public"),
    rights_evidence: Optional[str] = Form(None),
    ground_truth_text: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
) -> Dict[str, Any]:
    """Secure document upload and ingestion endpoint enforcing rights hygiene and security constraints."""
    config = get_config()

    # Validate document_id pattern
    if not re.match(r"^[a-zA-Z0-9_\-]+$", document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document_id: must contain only alphanumeric characters, underscores, and hyphens.",
        )

    # Validate filename and extension
    filename = Path(file.filename or "unknown").name  # Sanitize directory traversal
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read and enforce file size limit
    content = await file.read()
    if len(content) > config.max_upload_size_bytes:
        msg = f"File exceeds maximum upload limit of {config.max_upload_size_bytes} bytes."
        if config.is_vercel:
            msg += " Vercel serverless functions enforce a 4.5MB payload limit. Archival assets larger than 4MB must use direct-to-object-storage pre-signed URLs or the Northflank/on-prem intake pipeline."
        raise HTTPException(
            status_code=413,
            detail=msg,
        )

    # Enforce rights evidence for public and verified
    if rights_status in ("public", "verified") and not rights_evidence:
        raise HTTPException(
            status_code=422,
            detail=f"Rights status '{rights_status}' strictly requires --rights-evidence statutory or custodial citation.",
        )

    # Save raw file
    dest_path = config.raw_dir / f"{document_id}{ext}"
    with open(dest_path, "wb") as f:
        f.write(content)

    rel_local_path = str(dest_path.relative_to(config.repo_root)).replace("\\", "/")
    assigned_script = script or ("Deva" if language in ("hin", "mar") else "Latn")

    manifest = create_manifest(
        document_id=document_id,
        title=title,
        source_organization=source_organization,
        source_url=source_url,
        language=language,
        script=assigned_script,
        rights_status=rights_status,  # type: ignore
        rights_evidence=rights_evidence or "Pending verification",
        local_path=rel_local_path,
        page_count=1,
        notes=notes,
        repo_root=config.repo_root,
    )
    saved_manifest = save_manifest(manifest, output_dir=config.manifests_dir)

    # Save ground-truth if provided
    if ground_truth_text:
        gt_file = config.ground_truth_dir / f"{document_id}_p0001.json"
        gt_data = {
            "document_id": document_id,
            "page_id": f"{document_id}_p0001",
            "reference_text": ground_truth_text,
            "language": language,
            "script": assigned_script,
            "annotator": "Web Ingestion Specialist",
            "verification_status": "verified",
            "regions": [],
        }
        with open(gt_file, "w", encoding="utf-8") as f:
            json.dump(gt_data, f, indent=2)

    return {
        "status": "success",
        "message": f"Successfully ingested '{document_id}'.",
        "manifest": manifest.model_dump(),
        "manifest_path": str(saved_manifest),
    }


# ---------------------------------------------------------
# Search & Retrieval (E2 Preview / Demo)
# ---------------------------------------------------------

@app.get("/api/v1/search", tags=["Search & Retrieval"])
async def search_archive(
    q: str = Query(..., description="Query string to search across archival texts"),
    engine: str = Query("hybrid", description="Retrieval strategy: bm25, ngram, dense, or hybrid"),
    top_k: int = Query(5, ge=1, le=50, description="Maximum number of hits to return"),
) -> Dict[str, Any]:
    """Queries indexed archival documents using lexical, fuzzy, or dense retrieval."""
    config = get_config()
    selected_engine = _engines.get(engine.lower())
    if not selected_engine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Engine '{engine}' not supported. Choose from: {list(_engines.keys())}",
        )

    t0 = time.perf_counter()
    hits = selected_engine.search(q, top_k=top_k)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "execution_mode": f"{config.execution_mode}_SYNTHETIC" if config.execution_mode == "DEMO" else config.execution_mode,
        "disclaimer": "DEMO / SYNTHETIC DATA — NOT VALIDATED EMPIRICAL HISTORICAL RESULTS",
        "query": q,
        "engine": selected_engine.name,
        "duration_ms": round(duration_ms, 2),
        "total_hits": len(hits),
        "hits": [
            {
                "page_id": h.page_id,
                "score": round(h.score, 4),
                "text_snippet": h.text[:300] + ("..." if len(h.text) > 300 else ""),
            }
            for h in hits
        ],
    }


# ---------------------------------------------------------
# Evidence-Grounded QA & Visual Attribution (E3 Preview / Demo)
# ---------------------------------------------------------

class QuestionRequest(BaseModel):
    question: str = Field(..., description="Archival inquiry question")


@app.post("/api/v1/qa", tags=["Attribution & QA"])
async def answer_question(req: QuestionRequest) -> Dict[str, Any]:
    """Generates an evidence-grounded answer with token bounding boxes or triggers an algorithmic refusal."""
    config = get_config()
    if not _qa_pipeline:
        raise HTTPException(status_code=500, detail="QA pipeline not initialized.")

    ans = _qa_pipeline.answer_question(req.question)

    return {
        "execution_mode": f"{config.execution_mode}_SYNTHETIC" if config.execution_mode == "DEMO" else config.execution_mode,
        "disclaimer": "DEMO / SYNTHETIC DATA — NOT VALIDATED EMPIRICAL HISTORICAL RESULTS",
        "question": ans.question,
        "is_refusal": ans.is_refusal,
        "refusal_reason": ans.refusal_reason,
        "answer_text": ans.answer_text,
        "citations": [
            {
                "document_id": c.citation.document_id,
                "page_id": c.citation.page_id,
                "quote_span": c.citation.quote_span,
                "bbox": c.citation.bbox,
                "confidence": c.citation.confidence,
            }
            for c in ans.claims
            if c.citation
        ],
    }


# ---------------------------------------------------------
# Benchmark Status Endpoints
# ---------------------------------------------------------

@app.get("/api/v1/benchmarks/status", tags=["Benchmarks"])
async def get_benchmarks_status() -> Dict[str, Any]:
    """Returns milestone gates and empirical status summary."""
    return {
        "phases": {
            "E0": {"name": "Corpus & Rights Intake", "status": "PASS"},
            "E1": {"name": "Archival OCR Benchmark", "status": "BLOCKED (Host binary & authentic degraded scans pending)"},
            "E2": {"name": "Resilient Retrieval Benchmark", "status": "LOCKED (Gated on empirical E1 completion)"},
            "E3": {"name": "Attribution & Citation Grounding", "status": "LOCKED (Gated on empirical E1/E2 validation)"},
            "E4": {"name": "Multilingual Translation & TTS", "status": "READY (Gated)"},
            "E5": {"name": "Institutional Deployment & Kiosk", "status": "READY (Gated)"},
        },
        "research_integrity": "No synthetic or mock metrics are presented as real historical evidence.",
    }


@app.get("/api/v1/benchmarks/{phase}", tags=["Benchmarks"])
async def get_benchmark_result(phase: str) -> Dict[str, Any]:
    """Returns machine-readable JSON result file for a given benchmark phase (e1, e2, or e3)."""
    config = get_config()
    file_map = {
        "e1": "e1_ocr_results.json",
        "e2": "e2_retrieval_results.json",
        "e3": "e3_attribution_results.json",
    }
    filename = file_map.get(phase.lower())
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark results for phase '{phase}' not found.",
        )
    target_file = config.results_dir / filename
    if not target_file.is_file():
        target_file = config.repo_root / "results" / filename

    if not target_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark results for phase '{phase}' not found.",
        )
    with open(target_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# Interactive Archival Explorer (DEMO Interface)
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
async def serve_demo_ui():
    """Serves a responsive, accessible HTML/JS web interface for SIH judges and archival researchers."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIH26096 — Digital Heritage Archive</title>
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-light: #3b82f6;
            --accent: #d97706;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --danger-bg: #fef2f2;
            --danger-border: #f87171;
            --danger-text: #991b1b;
            --warning-bg: #fffbeb;
            --warning-border: #fcd34d;
            --warning-text: #92400e;
            --success-bg: #f0fdf4;
            --success-border: #86efac;
            --success-text: #166534;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background: var(--bg); color: var(--text); line-height: 1.5; padding-bottom: 40px; }
        header { background: var(--primary); color: white; padding: 1.25rem 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header-title { font-size: 1.35rem; font-weight: 700; display: flex; align-items: center; gap: 10px; }
        .header-sub { font-size: 0.85rem; color: #cbd5e1; margin-top: 4px; }
        
        .disclaimer-banner {
            background: var(--warning-bg);
            border-bottom: 2px solid var(--warning-border);
            color: var(--warning-text);
            padding: 0.75rem 2rem;
            font-size: 0.875rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
        @media (max-width: 900px) { .container { grid-template-columns: 1fr; } }

        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .card-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: var(--primary); display: flex; align-items: center; justify-content: space-between; }
        
        .search-box { display: flex; gap: 8px; margin-bottom: 1rem; }
        input[type="text"] { flex: 1; padding: 0.6rem 0.8rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.95rem; }
        select { padding: 0.6rem; border: 1px solid var(--border); border-radius: 6px; background: white; }
        button { background: var(--primary); color: white; border: none; border-radius: 6px; padding: 0.6rem 1.2rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        button:hover { background: var(--primary-light); }

        .result-item { border-left: 3px solid var(--primary-light); padding: 0.75rem; margin-bottom: 0.75rem; background: #f1f5f9; border-radius: 0 6px 6px 0; }
        .result-meta { font-size: 0.8rem; color: var(--text-muted); display: flex; justify-content: space-between; margin-bottom: 4px; }
        .result-text { font-size: 0.9rem; }

        .citation-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 0.75rem; margin-top: 0.75rem; }
        .citation-badge { display: inline-block; background: #2563eb; color: white; font-size: 0.75rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; }

        .gate-pill { display: inline-block; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 12px; }
        .gate-pass { background: var(--success-bg); border: 1px solid var(--success-border); color: var(--success-text); }
        .gate-blocked { background: var(--danger-bg); border: 1px solid var(--danger-border); color: var(--danger-text); }
        .gate-locked { background: var(--warning-bg); border: 1px solid var(--warning-border); color: var(--warning-text); }

        .gate-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .gate-table td { padding: 8px 4px; border-bottom: 1px solid var(--border); }

        .refusal-alert { background: var(--danger-bg); border: 1px solid var(--danger-border); color: var(--danger-text); padding: 0.75rem; border-radius: 6px; font-size: 0.9rem; font-weight: 600; }
    </style>
</head>
<body>

    <header>
        <div class="header-title">
            <span>🏛️ SIH26096: Digital Heritage Archive & Knowledge Platform</span>
        </div>
        <div class="header-sub">AI-Powered Institutional Archive for Memorials, Manuscripts & Dr. Ambedkar Writings</div>
    </header>

    <div class="disclaimer-banner">
        <span>⚠️ <strong>DEMO & SYNTHETIC MODE</strong>: This instance runs on verified synthetic fixtures to demonstrate pipeline capabilities without masquerading as historical scan benchmarks.</span>
        <span class="gate-pill gate-pass">Northflank Docker Ready</span>
    </div>

    <div class="container">
        <main>
            <!-- Search & Retrieval -->
            <div class="card">
                <div class="card-title">
                    <span>🔍 Resilient Document Retrieval (E2 Preview)</span>
                    <span class="gate-pill gate-locked">Benchmark Locked</span>
                </div>
                <div class="search-box">
                    <input type="text" id="search-input" value="Writings and Speeches Vasant Moon" placeholder="Search archive text (supports corrupted OCR)...">
                    <select id="search-engine">
                        <option value="hybrid">Hybrid (RRF k=60)</option>
                        <option value="bm25">Lexical (BM25)</option>
                        <option value="ngram">Fuzzy (3-Gram)</option>
                        <option value="dense">Dense (BGE-M3 Mock)</option>
                    </select>
                    <button onclick="executeSearch()">Search</button>
                </div>
                <div id="search-results">
                    <div style="color: var(--text-muted); font-size: 0.9rem;">Click 'Search' to query indexed documents.</div>
                </div>
            </div>

            <!-- Evidence Grounded QA & Attribution -->
            <div class="card">
                <div class="card-title">
                    <span>📑 Evidence-Grounded QA & Visual Attribution (E3 Preview)</span>
                    <span class="gate-pill gate-locked">Benchmark Locked</span>
                </div>
                <div class="search-box">
                    <input type="text" id="qa-input" value="Who compiled Volume 1 of Dr. Ambedkar's Writings and Speeches?" placeholder="Ask archival question...">
                    <button onclick="executeQA()">Ask Question</button>
                </div>
                <div id="qa-results">
                    <div style="color: var(--text-muted); font-size: 0.9rem;">Answers are strictly grounded in retrieved source tokens with visual bounding-box coordinates.</div>
                </div>
            </div>
        </main>

        <aside>
            <!-- Operational Gates -->
            <div class="card">
                <div class="card-title">
                    <span>⚙️ Research Milestone Gates</span>
                </div>
                <table class="gate-table">
                    <tr><td><strong>E0: Corpus & Rights</strong></td><td><span class="gate-pill gate-pass">PASS (Metadata)</span></td></tr>
                    <tr><td><strong>E1: Archival OCR</strong></td><td><span class="gate-pill gate-blocked">BLOCKED (Host Bin)</span></td></tr>
                    <tr><td><strong>E2: Retrieval</strong></td><td><span class="gate-pill gate-locked">LOCKED</span></td></tr>
                    <tr><td><strong>E3: Attribution</strong></td><td><span class="gate-pill gate-locked">LOCKED</span></td></tr>
                    <tr><td><strong>E4: Multilingual</strong></td><td><span class="gate-pill gate-pass">READY</span></td></tr>
                    <tr><td><strong>E5: Hardware / Kiosk</strong></td><td><span class="gate-pill gate-pass">READY</span></td></tr>
                </table>
                <div style="margin-top: 1rem; font-size: 0.75rem; color: var(--text-muted);">
                    <strong>Research Integrity Rule:</strong> Rights/provenance metadata validation is MEASURED. Legal authorization for a specific corpus is NOT ESTABLISHED BY SOFTWARE TEST. E2 and E3 benchmarks are locked from official ranking until authentic historical scans are ingested and OCR'd on host hardware.
                </div>
            </div>

            <!-- System Diagnostics -->
            <div class="card">
                <div class="card-title">
                    <span>🩺 Host System Diagnostics</span>
                </div>
                <div id="diagnostics-info" style="font-size: 0.85rem; color: var(--text-muted);">
                    Loading system status...
                </div>
            </div>
        </aside>
    </div>

    <script>
        async function fetchDiagnostics() {
            try {
                const res = await fetch('/api/v1/diagnostics');
                const data = await res.json();
                document.getElementById('diagnostics-info').innerHTML = `
                    <div><strong>Service:</strong> ${data.service}</div>
                    <div><strong>Mode:</strong> ${data.configuration.execution_mode}</div>
                    <div><strong>Tesseract:</strong> ${data.ocr_host_engine.available ? '✅ Available' : '⚠️ Missing Host Binary'}</div>
                    <div><strong>Device:</strong> ${data.ocr_host_engine.configured_device.toUpperCase()}</div>
                    <div><strong>Storage Vol:</strong> ${data.storage.archive_data_dir.writable ? '✅ Persistent & Writable' : '❌ Read-Only'}</div>
                `;
            } catch (err) {
                document.getElementById('diagnostics-info').innerText = 'Diagnostics unavailable.';
            }
        }

        async function executeSearch() {
            const query = document.getElementById('search-input').value;
            const engine = document.getElementById('search-engine').value;
            const resDiv = document.getElementById('search-results');
            resDiv.innerHTML = 'Searching...';

            try {
                const res = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}&engine=${engine}&top_k=5`);
                const data = await res.json();
                if (data.hits && data.hits.length > 0) {
                    resDiv.innerHTML = data.hits.map(h => `
                        <div class="result-item">
                            <div class="result-meta">
                                <span>📄 <strong>${h.page_id}</strong></span>
                                <span>Score: ${h.score} (${data.duration_ms} ms)</span>
                            </div>
                            <div class="result-text">${h.text_snippet}</div>
                        </div>
                    `).join('');
                } else {
                    resDiv.innerHTML = '<div style="color: var(--text-muted);">No matching archival documents found.</div>';
                }
            } catch (err) {
                resDiv.innerHTML = '<div style="color: var(--danger-text);">Search request failed.</div>';
            }
        }

        async function executeQA() {
            const query = document.getElementById('qa-input').value;
            const resDiv = document.getElementById('qa-results');
            resDiv.innerHTML = 'Synthesizing evidence-grounded answer...';

            try {
                const res = await fetch('/api/v1/qa', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: query })
                });
                const data = await res.json();
                if (data.is_refusal) {
                    resDiv.innerHTML = `
                        <div class="refusal-alert">
                            ⚠️ Algorithmic Refusal: ${data.refusal_reason || 'Insufficient archival evidence'}.
                            <div style="font-size: 0.8rem; font-weight: normal; margin-top: 4px;">
                                The system refused to hallucinate an answer because retrieved relevance fell below the verification threshold.
                            </div>
                        </div>
                    `;
                } else {
                    let citationsHtml = '';
                    if (data.citations && data.citations.length > 0) {
                        citationsHtml = data.citations.map(c => `
                            <div class="citation-box">
                                <span class="citation-badge">Citation: ${c.page_id}</span>
                                <div style="font-size: 0.85rem; margin-top: 4px;"><strong>Target Quote:</strong> "${c.quote_span}"</div>
                                <div style="font-size: 0.8rem; color: var(--text-muted);">Bounding Box: [x:${c.bbox[0]}, y:${c.bbox[1]}, w:${c.bbox[2]}, h:${c.bbox[3]}] (Confidence: ${c.confidence}%)</div>
                            </div>
                        `).join('');
                    }
                    resDiv.innerHTML = `
                        <div style="margin-bottom: 0.75rem; font-weight: 500;">${data.answer_text}</div>
                        ${citationsHtml}
                    `;
                }
            } catch (err) {
                resDiv.innerHTML = '<div style="color: var(--danger-text);">QA request failed.</div>';
            }
        }

        fetchDiagnostics();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
