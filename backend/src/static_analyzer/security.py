"""
Light-weight security heuristics for the static-analysis pipeline.

* run_security_checks – stub for bandit/gosec/trivy-like scanners
* find_secrets        – quick regex sweep for hard-coded secrets / keys
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# “Generic” risky patterns you might want a real scanner for
# ──────────────────────────────────────────────────────────────────────────────
BAD_PATTERNS: list[str] = [
    "eval(",
    "exec(",
    "pickle.load",          # arbitrary code execution risk
    "subprocess",
    "os.system",
]

# ──────────────────────────────────────────────────────────────────────────────
# Regex patterns for secrets (very broad – false-positives preferred)
# ──────────────────────────────────────────────────────────────────────────────
SECRET_PATTERNS: dict[str, str] = {
    "AWS key"     : r"AKIA[0-9A-Z]{16}",
    "Slack token" : r"xox[baprs]-[0-9a-zA-Z]{10,48}",
    "Generic key" : r"(?i)secret[_-]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9/+]{32,}['\"]",
    "Password"    : r"(?i)password\s*[:=]\s*['\"][^'\"]+['\"]",
}

# ------------------------------------------------------------------------------
# API
# ------------------------------------------------------------------------------

def run_security_checks(repo_path: Path) -> Dict[str, List[str]]:
    """
    Very small substitute for Bandit / Trivy / osv-scanner.

    Returns
    -------
    {
        "findings": [...],   # list[str] – everything we spotted
        "warnings": [...],   # list[str] – subset that should affect grading
    }
    """
    logger.debug("Running dummy security checks on %s", repo_path)

    findings: list[str] = []

    # ── scan *.py for “dangerous” calls ───────────────────────────────────────
    for file in repo_path.rglob("*.py"):
        try:
            for i, line in enumerate(file.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                for pattern in BAD_PATTERNS:
                    if pattern in line:
                        findings.append(f"{file.relative_to(repo_path)}:{i} contains risky pattern '{pattern}'")
        except Exception:
            # unreadable file – skip
            continue

    # ── flag Dockerfiles that run as root ─────────────────────────────────────
    for dockerfile in repo_path.rglob("[Dd]ockerfile"):
        if "USER root" in dockerfile.read_text(errors="ignore"):
            findings.append(f"{dockerfile.relative_to(repo_path)} runs as root")

    return {
        "findings": findings,
        "warnings": findings,   # for now treat them the same
    }


def find_secrets(repo_path: Path) -> List[str]:
    """
    Naïve grep for high-entropy strings or well-known token formats.

    Returns
    -------
    list[str] – *relative* file paths that look suspicious.
    """
    logger.debug("Scanning %s for hard-coded secrets", repo_path)
    secret_hits: set[str] = set()

    for file in repo_path.rglob("*.*"):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:      # binary / unreadable
            continue

        for name, pattern in SECRET_PATTERNS.items():
            if re.search(pattern, text):
                secret_hits.add(str(file.relative_to(repo_path)))
                logger.debug("Potential %s found in %s", name, file)
                break  # one hit is enough for this file

    return sorted(secret_hits)
