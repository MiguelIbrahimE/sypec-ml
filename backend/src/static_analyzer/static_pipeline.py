# backend/src/static_analyzer/static_pipeline.py
"""
Refactored end-to-end static-analysis pipeline.

 ▪ adds API-usage scan, secrets scan, language mix, energy stdev + plot
 ▪ produces richer context for the LaTeX template consumed by report.builder
 ▪ silences matplotlib’s verbose font-discovery DEBUG spam
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from statistics import stdev, median
from typing import Dict, List, Any

import matplotlib
matplotlib.use("Agg")  # headless backend for container

# ── tame Matplotlib chatter (font_manager etc.) ───────────────────────────────
logging.getLogger("matplotlib").setLevel(logging.INFO)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

import matplotlib.pyplot as plt  # noqa: E402  (after backend switch)

# ── internal helpers ──────────────────────────────────────────────────────────
from ..report.builder import generate_pdf_report
from ..utils.git import clone_repo  # noqa: F401  (kept for API parity)

from .digest import get_repo_digest
from .code_stats import analyze_code_stats, EXT_LANGUAGE_MAP
from .code_smells import detect_code_smells
from .docker_stats import estimate_docker_usage
from .energy_model import estimate_energy
from .security import run_security_checks, find_secrets
from .purpose import infer_project_purpose, infer_deployment_context
from .test_coverage import estimate_test_coverage
from .hardware_profiles import get_live_profile

logger = logging.getLogger(__name__)

# output folder (mounted to host via docker-compose volume)
REPORT_DIR = Path("data/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────────────────────
def _language_mix(digest: Dict[str, Any]) -> Dict[str, int]:
    """Return {Language: LOC} sorted descending."""
    mix: Dict[str, int] = {}
    for ext, loc in digest["extensions"].items():
        lang = EXT_LANGUAGE_MAP.get(ext, ext.lstrip(".").upper())
        mix[lang] = mix.get(lang, 0) + loc
    return dict(sorted(mix.items(), key=lambda kv: kv[1], reverse=True))


def _dominant_lang(lang_mix: Dict[str, int]) -> str:
    return max(lang_mix, key=lang_mix.get) if lang_mix else "Unknown"


def _scan_apis(repo: Path) -> List[str]:
    """Tiny heuristic: search for common SDK imports or base-URLs."""
    api_patterns = {
        "OpenAI": r"(openai\.com|openai\s+import|Configuration\(api_key)",
        "Stripe": r"(stripe\.com|import\s+stripe)",
        "Twilio": r"(api\.twilio\.com|import\s+twilio)",
        "AWS": r"(boto3|aws_secret_access_key)",
        "GCP": r"(google\.cloud|GOOGLE_APPLICATION_CREDENTIALS)",
    }
    hits: set[str] = set()
    for file in repo.rglob("*.*"):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue  # binary or unreadable
        for name, pat in api_patterns.items():
            if re.search(pat, text, re.I):
                hits.add(name)
    return sorted(hits)


def _plot_energy(model: Dict[int, float], out_dir: Path) -> Path:
    """Generate a PNG chart and return its path."""
    users, kwh = zip(*sorted(model.items()))
    fig = plt.figure(figsize=(4.5, 2.5))
    plt.plot(users, kwh, marker="o", linewidth=2)
    plt.fill_between(users, kwh, alpha=0.15)
    plt.title("Estimated daily energy vs. active users")
    plt.xlabel("Concurrent users")
    plt.ylabel("kWh / day")
    plt.grid(True, linestyle=":")
    fig.tight_layout()
    plot_path = out_dir / "energy.png"
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)
    return plot_path


# ──────────────────────────────────────────────────────────────────────────────
# Public orchestrator
# ──────────────────────────────────────────────────────────────────────────────
def run_static_pipeline(repo_path: Path) -> Dict[str, Any]:
    """
    Run all offline analysers and generate a PDF + JSON payload.

    The repository must already be cloned locally.
    """
    logger.info("📂  Static analysis on %s", repo_path)

    # 1. Digest ----------------------------------------------------------------
    digest = get_repo_digest(repo_path)

    # 2. Statistics & QA -------------------------------------------------------
    code_stats = analyze_code_stats(digest, repo_path)
    code_smells = detect_code_smells(str(repo_path))
    test_coverage = estimate_test_coverage(repo_path)
    security_report = run_security_checks(repo_path)
    secrets_found = find_secrets(repo_path)

    # 3. Languages -------------------------------------------------------------
    lang_mix = _language_mix(digest)
    dominant_lang = _dominant_lang(lang_mix)

    # 4. Purpose / context / hardware -----------------------------------------
    purpose = infer_project_purpose(repo_path)
    context = infer_deployment_context(digest)  # “desktop” / “cloud” / “mobile”
    hw_profile = get_live_profile(context)

    # 5. Docker footprint + energy --------------------------------------------
    docker_stats = estimate_docker_usage(repo_path)
    energy_model = estimate_energy(code_stats, docker_stats, context)
    energy_stdev = stdev(energy_model.values()) if len(energy_model) > 1 else 0.0
    energy_median = median(energy_model.values())

    # 6. Visualisation ---------------------------------------------------------
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_base = REPORT_DIR / f"report_{repo_path.name}_{timestamp}"
    report_base.mkdir(parents=True, exist_ok=True)
    energy_plot = _plot_energy(energy_model, report_base)

    # 7. APIs & warnings -------------------------------------------------------
    apis_used = _scan_apis(repo_path)
    warnings_all = (
            code_stats.get("warnings", [])
            + security_report.get("warnings", [])
            + code_smells
            + (["Secrets committed"] if secrets_found else [])
    )
    score = max(1, min(100, 100 - 5 * len(warnings_all)))
    grade = (
        "A+++" if score >= 95 else
        "A"    if score >= 85 else
        "B+"   if score >= 75 else
        "B"    if score >= 65 else
        "C"    if score >= 50 else
        "D"    if score >= 30 else
        "F"
    )

    # 8. PDF generation --------------------------------------------------------
    try:
        pdf_path = generate_pdf_report(
            output_base=report_base,
            ctx=dict(
                repo_name=repo_path.name,
                repo_url=str(repo_path),
                purpose=purpose,
                hardware=hw_profile,
                digest=digest,
                code_stats=code_stats,
                docker_stats=docker_stats,
                energy_profile=energy_model,
                energy_stdev=energy_stdev,
                energy_plot=energy_plot.name,
                security=security_report.get("findings", []),
                coverage=test_coverage,
                smells=code_smells,
                warnings=warnings_all,
                score=score,
                grade=grade,
                dominant_lang=dominant_lang,
                languages=lang_mix,
                apis_used=apis_used,
                secrets_found=secrets_found,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("PDF generation failed: %s", exc, exc_info=True)
        pdf_path = None

    # 9. JSON response ---------------------------------------------------------
    return {
        "intro": f"Static analysis of {repo_path.name}",
        "purpose": purpose[:280],
        "hardware": hw_profile,
        "score": score,
        "grade": grade,
        "kwh": energy_model,
        "test_coverage": test_coverage,
        "bullets": warnings_all[:6],
        "pdf_url": f"/reports/{pdf_path.name}" if pdf_path else None,
    }
