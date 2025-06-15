# backend/src/api.py
from __future__ import annotations

import logging
import traceback
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from backend.src.static_analyzer.clone import clone_repo
from backend.src.static_analyzer.static_pipeline import run_static_pipeline

# ─────────────────────────── Logging ────────────────────────────
LOG_FILE = Path("analyzer_debug.log")
logging.basicConfig(
    level=logging.DEBUG,                              # ➜ change to INFO in prod
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE)],
)

# ─────────────────────────── FastAPI app ────────────────────────
app = FastAPI(title="Sypec – Static Auditor")

# Serve generated PDFs:  http://<host>:8000/static/reports/<file>.pdf
app.mount(
    "/static/reports",
    StaticFiles(directory="data/reports", html=False),
    name="reports",
)

# ─────────────────────────── Request model ──────────────────────
class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl

# ─────────────────────────── Route ──────────────────────────────
@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    ts = datetime.utcnow().isoformat(timespec="seconds")
    logging.info("[%s] request: %s", ts, req.repo_url)

    try:
        logging.debug("Cloning repository …")
        repo_path = clone_repo(req.repo_url)          # local temp dir
        logging.debug("Repository cloned → %s", repo_path)

        logging.debug("Running static pipeline …")
        result = run_static_pipeline(repo_path)

        response = {"repo_url": str(req.repo_url), **result}
        logging.debug("Response → %s", response)
        return response

    except Exception as exc:
        logging.error("Pipeline failed:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Static analysis failed: {type(exc).__name__}: {exc}",
        ) from exc
