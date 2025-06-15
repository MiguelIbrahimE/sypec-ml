# backend/src/api.py

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from backend.src.static_analyzer.clone import clone_repo
from backend.src.static_analyzer.static_pipeline import run_static_pipeline
import logging
import traceback
from datetime import datetime

# ─── Logging Config ─────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO in prod
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),  # prints to console
        logging.FileHandler("analyzer_debug.log")  # saves to file
    ]
)

# ─── FastAPI App ────────────────────────────────────────
app = FastAPI(title="Sypec – Static Auditor")

# ─── Request Schema ─────────────────────────────────────
class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl

# ─── Route: Analyze ─────────────────────────────────────
@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    timestamp = datetime.utcnow().isoformat()
    logging.info(f"[{timestamp}] Received request: {req.repo_url}")

    try:
        logging.debug("Cloning repository...")
        repo_path = clone_repo(req.repo_url)
        logging.debug(f"Repository cloned at: {repo_path}")

        logging.debug("Running static pipeline...")
        result = run_static_pipeline(repo_path)
        logging.info("Static analysis completed successfully.")

        response = {"repo_url": str(req.repo_url), **result}
        logging.debug(f"Response: {response}")
        return response

    except Exception as exc:
        logging.error("An error occurred during analysis.")
        logging.error(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Static analysis failed: {type(exc).__name__}: {exc}"
        ) from exc
