# -*- coding: utf-8 -*-
"""
Quick-n-dirty language mix detector.

We count extensions and return a dict
    {"python": 37, "typescript": 15, "yaml": 2, …}
plus the dominant language name.
"""
from collections import Counter
from pathlib import Path
from typing import Dict, Tuple

_EXT2LANG = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
}


def detect_languages(root: Path) -> Tuple[Dict[str, int], str]:
    counts = Counter()

    for path in root.rglob("*.*"):
        if path.is_file():
            lang = _EXT2LANG.get(path.suffix.lower())
            if lang:
                counts[lang] += 1

    dominant = counts.most_common(1)[0][0] if counts else "unknown"
    return dict(counts), dominant
