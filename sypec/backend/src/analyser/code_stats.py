"""
Static-analysis helpers.
Uses `cloc` for SLOC, `radon` for complexity & maintainability, etc.
"""
from pathlib import Path
import json
import subprocess
from statistics import mean

def _run_cloc(repo: Path) -> dict:
    """Return cloc --json output as dict."""
    result = subprocess.run(
        ["cloc", "--json", "--quiet", str(repo)], text=True, capture_output=True, check=True
    )
    return json.loads(result.stdout)

def _calc_complexity(repo: Path) -> float:
    """Radon cyclomatic complexity average (simplified)."""
    result = subprocess.run(
        ["radon", "cc", "-s", "-j", str(repo)], text=True, capture_output=True, check=True
    )
    cc_map = json.loads(result.stdout)
    return mean(score for files in cc_map.values() for (_, _, score) in files)

def collect_code_metrics(repo: Path) -> dict:
    """Return dict with lines_of_code, complexity, maintainability_index, etc."""
    cloc = _run_cloc(repo)
    complexity = _calc_complexity(repo)
    loc = cloc["SUM"]["code"]

    # Example maintainability (placeholder)
    maintainability = max(0, 100 - complexity)

    return {
        "loc": loc,
        "complexity": complexity,
        "maintainability": maintainability,
    }
