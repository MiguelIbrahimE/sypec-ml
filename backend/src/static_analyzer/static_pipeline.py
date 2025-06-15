import shutil
from pathlib import Path
from ..utils.git import clone_repo
from .digest import get_repo_digest
from .code_stats import analyze_code_stats
from .docker_stats import estimate_docker_usage
from .energy_model import estimate_energy
from .security import run_security_checks


def run_static_pipeline(repo_path: Path) -> dict:
    # Step 1: digest the repo
    digest = get_repo_digest(repo_path)

    # Step 2: static analyses
    code_stats = analyze_code_stats(digest)
    docker_stats = estimate_docker_usage(repo_path)
    energy_profile = estimate_energy(code_stats, docker_stats)
    security_report = run_security_checks(repo_path)

    # Step 3: synthesize results
    warnings = security_report.get("warnings", []) + code_stats.get("warnings", [])
    score = max(1, min(100, 100 - len(warnings) * 5))
    grade = (
        "A+++" if score >= 95 else
        "A" if score >= 85 else
        "B+" if score >= 75 else
        "B" if score >= 65 else
        "C" if score >= 50 else
        "D" if score >= 30 else
        "F"
    )

    # Step 4: report output
    return {
        "intro": f"Static analysis of {repo_path.name}",
        "score": score,
        "grade": grade,
        "kwh": energy_profile,
        "bullets": warnings[:6],  # cap to top 6
    }
