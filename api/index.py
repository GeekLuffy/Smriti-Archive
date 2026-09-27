"""
Vercel Serverless Function Entrypoint for SIH26096 Archival System.

Exposes the FastAPI application instance for serverless HTTP routing on Vercel.
"""

import os
from pathlib import Path
import sys

# Ensure src/ is on python path for Vercel execution environment
repo_root = Path(__file__).resolve().parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Default execution mode to DEMO in serverless environment if not set
os.environ.setdefault("EXECUTION_MODE", "DEMO")
os.environ.setdefault("APP_ENV", "vercel")

from sih_archive.api.app import app

__all__ = ["app"]
