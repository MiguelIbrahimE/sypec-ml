"""
Very light heuristic: look for common SDK imports / curl strings
and env-var names to guess outbound API dependencies.
Return a list of APIs (strings).
"""
import re
from pathlib import Path
from typing import List

_PATTERNS = {
    "openai": re.compile(r"\bopenai\b", re.I),
    "slack": re.compile(r"\bslack[_\-]?sdk\b|\bslack\.com/api", re.I),
    "stripe": re.compile(r"\bstripe\b", re.I),
    "aws": re.compile(r"\b(boto3|aws[-_]sdk|amazonaws\.com)\b", re.I),
    "github": re.compile(r"\bgithub\b.*(?:api|graphQL)", re.I),
}


def find_api_usage(root: Path) -> List[str]:
    hits = {name: 0 for name in _PATTERNS}

    for f in root.rglob("*.*"):
        if f.suffix.lower() in {".py", ".ts", ".js"} and f.stat().st_size < 256_000:
            try:
                text = f.read_text(errors="ignore")
            except Exception:  # pragma: no cover
                continue

            for name, pat in _PATTERNS.items():
                if pat.search(text):
                    hits[name] += 1

    return [k for k, v in hits.items() if v]
