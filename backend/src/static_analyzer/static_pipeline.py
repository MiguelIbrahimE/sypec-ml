# backend/src/static_analyzer/static_pipeline.py
"""
End-to-end static-analysis pipeline

▪ digests the repo (respecting .gitignore)  
▪ runs a bundle of lightweight, offline analysers  
▪ fetches a *live* hardware profile (Steam survey for desktop / placeholders for
  cloud & mobile) and produces a naïve energy-usage model  
▪ renders a polished PDF report (LaTeX → PDF) and returns its relative URL

Any expensive or network-bound step is cached or guarded by time-outs so the
route stays responsive inside the container.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# ── internal helpers ────────────────────────────────────────────────────
from ..report.builder import generate_pdf_report
from ..utils.git import clone_repo

from .digest import get_repo_digest
from .code_stats import analyze_code_stats
from .code_smells import detect_code_smells
from .docker_stats import estimate_docker_usage
from .energy_model import estimate_energy
from .security import run_security_checks
from .purpose import (
    infer_project_purpose,
    infer_deployment_context,  # desktop / cloud / mobile
)
from .test_coverage import estimate_test_coverage
from .hardware_profiles import get_live_profile  # live Steam survey cache

logger = logging.getLogger(__name__)

# output folder (mounted to host via docker-compose volume)
REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ── public API ──────────────────────────────────────────────────────────
def run_static_pipeline(repo_path: Path) -> Dict[str, Any]:
    """
    Orchestrate all offline analysers and build the response payload.
    `repo_path` is the *local* path of the already-cloned repository.
    """
    logger.debug("📂  Static pipeline started on %s", repo_path)

    # ── 1. file digest ────────────────────────────────────────────────
    logger.debug("Step 1 – digesting repository …")
    digest = get_repo_digest(repo_path)
    logger.info(
        "Digest done: %s files, %s LOC",
        len(digest["files"]),
        digest["total_loc"],
    )

    # ── 2. basic code statistics ─────────────────────────────────────
    logger.debug("Step 2 – code statistics …")
    code_stats = analyze_code_stats(digest, repo_path)
    logger.debug("Code stats → %s", code_stats)

    # ── 3. docker footprint estimate ─────────────────────────────────
    docker_stats = estimate_docker_usage(repo_path)
    logger.debug("Docker estimate → %s", docker_stats)

    # ── 4. project purpose & deployment context ──────────────────────
    purpose = infer_project_purpose(repo_path)
    context = infer_deployment_context(digest)  # “desktop” / “cloud” / …
    hw_profile = get_live_profile(context)
    logger.debug("Purpose=%s · Context=%s · HW=%s", purpose, context, hw_profile)

    # ── 5. energy model  (sub-linear heuristic) ──────────────────────
    energy_profile = estimate_energy(
        code_stats,
        docker_stats,
        profile_hint=context,
    )
    logger.debug("Energy profile → %s kWh", energy_profile)

    # ── 6. security scan / test coverage / code smells ───────────────
    security_report = run_security_checks(repo_path)
    test_coverage = estimate_test_coverage(repo_path)
    code_smells = detect_code_smells(str(repo_path))
    logger.debug("Security=%s · Coverage=%s · Smells=%s", security_report, test_coverage, code_smells)

    # ── 7. scoring & grading ─────────────────────────────────────────
    security_warns: List[str] = (
        security_report.get("warnings", [])
        if isinstance(security_report, dict)
        else security_report
    )
    code_warns: List[str] = (
        code_stats.get("warnings", [])
        if isinstance(code_stats, dict)
        else code_stats
    )
    all_warnings: List[str] = security_warns + code_warns + code_smells

    score = max(1, min(100, 100 - len(all_warnings) * 5))
    grade = (
        "A+++" if score >= 95 else
        "A"    if score >= 85 else
        "B+"   if score >= 75 else
        "B"    if score >= 65 else
        "C"    if score >= 50 else
        "D"    if score >= 30 else
        "F"
    )
    logger.info("✅  Score=%s · Grade=%s · Warnings=%s", score, grade, len(all_warnings))

    # ── 8. LaTeX → PDF report ────────────────────────────────────────
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_base = REPORT_DIR / f"report_{repo_path.name}_{timestamp}"
    pdf_path = None
    try:
        pdf_path = generate_pdf_report(
            output_base=report_base,
            ctx={
                "repo_name": repo_path.name,
                "purpose": purpose,
                "hardware": hw_profile,
                "digest": digest,
                "code_stats": code_stats,
                "docker_stats": docker_stats,
                "energy_profile": energy_profile,
                "security": security_report,
                "coverage": test_coverage,
                "smells": code_smells,
                "score": score,
                "grade": grade,
            },
        )
        logger.debug("PDF generated at %s", pdf_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("PDF generation failed: %s", exc, exc_info=True)

    pdf_url = f"/static/reports/{pdf_path.name}" if pdf_path else None

    # ── 9. build JSON response ───────────────────────────────────────
    response: Dict[str, Any] = {
        "intro": f"Static analysis of {repo_path.name}",
        "purpose": purpose[:300],
        "hardware": hw_profile,
        "score": score,
        "grade": grade,
        "kwh": energy_profile,
        "test_coverage": test_coverage,
        "bullets": all_warnings[:6],  # top six issues
        "pdf_url": pdf_url,
    }
    logger.debug("Pipeline response → %s", response)
    return response
