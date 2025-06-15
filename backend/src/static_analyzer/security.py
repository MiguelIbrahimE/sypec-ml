# backend/src/static_analyzer/security.py
from typing import List
import os

BAD_PATTERNS = ["eval(", "exec(", "pickle.load", "subprocess", "os.system"]


def run_security_checks(repo_path: str) -> List[str]:
    findings = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            try:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        for pattern in BAD_PATTERNS:
                            if pattern in line:
                                findings.append(f"{file}:{i} contains risky pattern '{pattern}'")
            except Exception:
                continue
    return findings
