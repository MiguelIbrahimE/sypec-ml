# backend/src/static_analyzer/code_stats.py
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def analyze_code_stats(digest: dict, repo_path: Path) -> dict:
    logger.debug("Starting code stats analysis...")
    loc = digest.get("total_loc", 0)
    files = digest.get("files", [])

    issues = []
    if loc == 0:
        issues.append("Empty repository.")
    if loc > 100_000:
        issues.append("Repository is very large, consider modularizing.")
    if not any(f["ext"] in [".md", ".rst"] for f in files):
        issues.append("Missing documentation files.")

    # Example: count Python files
    python_files = [f for f in files if f["ext"] == ".py"]
    if len(python_files) < 2:
        issues.append("Few Python files detected.")

    logger.debug(f"Code analysis complete: LOC={loc}, Python files={len(python_files)}")
    return {
        "loc": loc,
        "file_count": len(files),
        "warnings": issues,
    }
