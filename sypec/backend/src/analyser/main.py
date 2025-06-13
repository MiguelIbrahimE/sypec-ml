"""
Pulls everything together:
1. Clone / update the repo in data/cache/
2. Run static code-quality checks           → code_metrics
3. Run energy & scaling simulation          → energy_projection
4. Call LLM for narrative explanations      → llm_notes
Returns a dict that report.tex.jinja is expecting.
"""
from pathlib import Path
from datetime import datetime
import subprocess
import tempfile

from .code_stats import collect_code_metrics
from .energy_model import project_energy_use
from .llm_helpers import draft_recommendations

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)


def _clone_or_update_repo(url: str) -> Path:
    """Clone repo into CACHE_DIR/<slug>. Returns the path."""
    repo_slug = url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = CACHE_DIR / repo_slug
    if repo_path.exists():
        subprocess.run(["git", "-C", str(repo_path), "pull", "--ff-only"], check=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1", url, str(repo_path)], check=True)
    return repo_path


def analyse_repo(url: str) -> dict:
    """Main façade called by the API layer."""
    repo_path = _clone_or_update_repo(url)

    code_metrics = collect_code_metrics(repo_path)
    energy_projection = project_energy_use(code_metrics)

    notes = draft_recommendations(code_metrics, energy_projection)

    return {
        "repo_name": repo_path.name,
        "analysis_date": datetime.utcnow().isoformat(),
        "code_metrics": code_metrics,
        "energy_projection": energy_projection,
        "recommendations": notes["bullets"],
        "sustainability_score": notes["score"],  # 0-100
    }
