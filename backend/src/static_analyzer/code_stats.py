# backend/src/static_analyzer/code_stats.py
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# File-extension → language map
# Extend this as needed for your repos
# ──────────────────────────────────────────────────────────────────────────────
EXT_LANGUAGE_MAP: dict[str, str] = {
    ".py":   "Python",
    ".ipynb": "Jupyter",
    ".js":   "JavaScript",
    ".jsx":  "JSX",
    ".ts":   "TypeScript",
    ".tsx":  "TSX",
    ".java": "Java",
    ".go":   "Go",
    ".rb":   "Ruby",
    ".rs":   "Rust",
    ".c":    "C",
    ".cpp":  "C++",
    ".h":    "C/C++ Header",
    ".cs":   "C#",
    ".php":  "PHP",
    ".scala": "Scala",
    ".kt":   "Kotlin",
    ".swift": "Swift",
    ".sh":   "Shell",
    ".dockerfile": "Dockerfile",
    ".yaml": "YAML",
    ".yml":  "YAML",
    ".json": "JSON",
}

__all__ = ["analyze_code_stats", "EXT_LANGUAGE_MAP"]

# ──────────────────────────────────────────────────────────────────────────────
# Main analysis entry point
# ──────────────────────────────────────────────────────────────────────────────
def analyze_code_stats(digest: dict, repo_path: Path) -> dict:
    """
    Build simple code-base statistics and lightweight heuristics.

    Parameters
    ----------
    digest : dict
        Result of `get_repo_digest` (file counts, LOC, etc.).
    repo_path : Path
        Absolute path to the checked-out repository.

    Returns
    -------
    dict
        {
            "loc": int,             # total lines of code
            "file_count": int,      # number of files scanned
            "warnings": list[str],  # heuristic issues / suggestions
        }
    """
    logger.debug("Starting code stats analysis...")
    loc   = digest.get("total_loc", 0)
    files = digest.get("files", [])

    issues: list[str] = []

    # Basic volume heuristics --------------------------------------------------
    if loc == 0:
        issues.append("Empty repository.")
    if loc > 100_000:
        issues.append("Repository is very large, consider modularizing.")

    # Documentation presence ---------------------------------------------------
    if not any(f["ext"] in [".md", ".rst"] for f in files):
        issues.append("Missing documentation files.")

    # Example language-specific check -----------------------------------------
    python_files = [f for f in files if f["ext"] == ".py"]
    if len(python_files) < 2:
        issues.append("Few Python files detected.")

    logger.debug(
        "Code analysis complete: LOC=%s, total files=%s, python_files=%s",
        loc, len(files), len(python_files)
    )

    return {
        "loc": loc,
        "file_count": len(files),
        "warnings": issues,
    }
