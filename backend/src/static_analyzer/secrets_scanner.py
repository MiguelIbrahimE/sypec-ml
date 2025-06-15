"""
Tiny fallback secrets scanner (does NOT replace truffle-hog etc.).
Flags obvious tokens in code.
"""
import re
from pathlib import Path
from typing import List

_SECRET_RE = re.compile(
    r"""
    (?P<name>[A-Z0-9_]{8,})      # ENV-like name
    \s*[:=]\s*
    ["']?
    (?P<val>sk[-_a-zA-Z0-9]{20,}|  # OpenAI / Stripe style
           AKIA[0-9A-Z]{16}|       # AWS key
           gh[pousr]_[0-9a-zA-Z]{36,})  # GitHub token
    """,
    re.X,
)


def scan_for_secrets(root: Path) -> List[str]:
    findings: List[str] = []

    for file in root.rglob("*"):
        if file.suffix.lower() in {".py", ".js", ".ts", ".env"} and file.stat().st_size < 200_000:
            try:
                text = file.read_text(errors="ignore")
            except Exception:  # pragma: no cover
                continue

            for m in _SECRET_RE.finditer(text):
                findings.append(f"{file}:{m.group('name')}=***")

    return findings[:20]  # cap noise
