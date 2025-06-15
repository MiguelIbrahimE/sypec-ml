# -*- coding: utf-8 -*-
"""
End-to-end static-analysis pipeline

• digests the repo (respecting .gitignore)
• runs a bundle of lightweight, offline analysers
• fetches a live hardware profile (Steam survey for desktop / placeholders for
  cloud & mobile) and produces a naïve energy-usage model
• renders a polished PDF report (LaTeX → PDF) that now contains a graph of the
  energy curve ± σ (std-dev)

Any expensive or network-bound step is cached or guarded by time-outs so the
route stays responsive inside the container.
"""
from __future__ import annotations

import logging
import statistics as _stats
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import matplotlib                            # <-- run-time dep
matplotlib.use("Agg")                        # headless
import matplotlib.pyplot as _plt             # noqa: E402

# ──────────── internal helpers ─────────────────────────────────────────
from ..report.builder import generate_pdf_report
from ..utils.git import clone_repo  # still used by /api, not here

from .digest             import get_repo_digest
from .code_stats         import analyze_code_stats
from .code_smells        import detect_code_smells
from .docker_stats       import estimate_docker_usage
from .energy_model       import estimate_energy
from .security           import run_security_checks
from .purpose            import infer_project_purpose, infer_deployment_context
from .test_coverage      import estimate_test_coverage
from .hardware_profiles  import get_live_profile
from .language_detector  import detect_languages
from .api_usage          import find_api_usage
from .secrets_scanner    import scan_for_secrets

logger = logging.getLogger(__name__)

# Output folder (mounted to host via docker-compose volume)
REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ──────────── helpers ─────────────────────────────────────────────────
def _plot_energy(curve: Dict[int, float], target: Path) -> None:
    """Save a simple log-log energy curve as PNG."""
    users = sorted(curve)
    vals  = [curve[u] for u in users]

    _plt.figure(figsize=(4, 3))
    _plt.loglog(users, vals, marker="o")
    _plt.grid(True, which="both", ls=":")
    _plt.xlabel("Active users")
    _plt.ylabel("kWh per day")
    _plt.tight_layout()
    _plt.savefig(target, dpi=200)
    _plt.close()


# ──────────── public API ──────────────────────────────────────────────
def run_static_pipeline(repo_path: Path) -> Dict[str, Any]:
    """Orchestrate all offline analysers and build the JSON + PDF payload."""
    logger.debug("📂  Static pipeline started on %s", repo_path)

    # 1. file digest ----------------------------------------------------
    digest = get_repo_digest(repo_path)
    logger.info("Digest done: %s files, %s LOC", len(digest["files"]), digest["total_loc"])

    # 2. language mix & basic stats ------------------------------------
    lang_breakdown, dominant_lang = detect_languages(repo_path)
    code_stats = analyze_code_stats(digest, repo_path)
    apis_used  = find_api_usage(repo_path)
    secrets    = scan_for_secrets(repo_path)
    client_heavy = "typescript" in lang_breakdown
    logger.debug("Langs=%s · APIs=%s · Secrets=%s", lang_breakdown, apis_used, len(secrets))

    # 3. docker footprint, purpose, context ----------------------------
    docker_stats = estimate_docker_usage(repo_path)
    purpose      = infer_project_purpose(repo_path)
    context      = infer_deployment_context(digest)
    hw_profile   = get_live_profile(context)

    # 4. energy model ---------------------------------------------------
    energy_profile = estimate_energy(
        code_stats,
        docker_stats,
        profile_hint=context,
        api_list=apis_used,
        client_heavy=client_heavy,
    )
    energy_stdev = _stats.pstdev(energy_profile.values()) if len(energy_profile) > 1 else 0.0

    # 5. security, tests, smells ---------------------------------------
    security_report = run_security_checks(repo_path)
    test_coverage   = estimate_test_coverage(repo_path)
    code_smells     = detect_code_smells(str(repo_path))

    # 6. scoring & warnings --------------------------------------------
    security_warns = security_report.get("warnings", []) if isinstance(security_report, dict) else security_report
    code_warns     = code_stats.get("warnings", [])    if isinstance(code_stats, dict)    else code_stats
    all_warnings   = security_warns + code_warns + code_smells + [f"Exposed secret: {s}" for s in secrets]

    score = max(1, min(100, 100 - len(all_warnings) * 5))
    grade = ("A+++" if score >= 95 else "A" if score >= 85 else "B+" if score >= 75
    else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 30 else "F")
    logger.info("✅  Score=%s · Grade=%s · Warnings=%s", score, grade, len(all_warnings))

    # 7. reporting ------------------------------------------------------
    ts          = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_base = REPORT_DIR / f"report_{repo_path.name}_{ts}"
    plot_path   = report_base.with_suffix("") / "energy_plot.png"
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    _plot_energy(energy_profile, plot_path)

    pdf_path = None
    try:
        pdf_path = generate_pdf_report(
            output_base=report_base,
            ctx={
                "repo_name": repo_path.name,
                "digest": digest,
                "purpose": purpose,
                "hardware": hw_profile,
                "docker_stats": docker_stats,
                "code_stats": code_stats,
                "languages": lang_breakdown,
                "dominant_lang": dominant_lang,
                "apis_used": apis_used,
                "secrets_found": secrets,
                "energy_profile": energy_profile,
                "energy_stdev": round(energy_stdev, 2),
                "security": security_report,
                "coverage": test_coverage,
                "smells": code_smells,
                "score": score,
                "grade": grade,
                "warnings": all_warnings,
                "energy_plot": plot_path.name,
            },
        )
        logger.debug("PDF generated at %s", pdf_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("PDF generation failed: %s", exc, exc_info=True)

    # 8. JSON -----------------------------------------------------------
    return {
        "intro":   f"Static analysis of {repo_path.name}",
        "purpose": purpose[:300],
        "hardware": hw_profile,
        "languages": lang_breakdown,
        "apis_used": apis_used,
        "secrets_found": secrets,
        "score":   score,
        "grade":   grade,
        "kwh":     energy_profile,
        "energy_stdev": energy_stdev,
        "test_coverage": test_coverage,
        "bullets": all_warnings[:6],
        "pdf_url": f"/reports/{pdf_path.relative_to(REPORT_DIR).parent.name}/{pdf_path.name}" if pdf_path else None,
    }
