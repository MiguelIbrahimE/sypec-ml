# backend/src/static_analyzer/code_stats.py
import os
from collections import Counter
from typing import Dict, Any

def analyze_code_stats(repo_path: str) -> Dict[str, Any]:
    loc_counter = Counter()
    ext_counter = Counter()

    for root, _, files in os.walk(repo_path):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    loc = len(lines)
                    ext = os.path.splitext(file)[-1].lower()
                    loc_counter[ext] += loc
                    ext_counter[ext] += 1
            except Exception:
                continue

    total_loc = sum(loc_counter.values())
    return {
        "total_loc": total_loc,
        "language_breakdown": dict(loc_counter),
        "filetype_count": dict(ext_counter),
    }

