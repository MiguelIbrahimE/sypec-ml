# backend/src/static_analyzer/digest.py
import os
from pathlib import Path
import pathspec


def load_gitignore(repo_path: Path) -> pathspec.PathSpec:
    ignore_file = repo_path / ".gitignore"
    if ignore_file.exists():
        with ignore_file.open() as f:
            patterns = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    return pathspec.PathSpec([])


def get_repo_digest(repo_path: str) -> dict:
    """Returns file metadata: paths, sizes, extensions, lines of code."""
    repo_path = Path(repo_path)
    spec = load_gitignore(repo_path)
    summary = {
        "files": [],
        "total_loc": 0,
        "extensions": {},
    }

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        rel_path = str(path.relative_to(repo_path))
        if spec.match_file(rel_path):
            continue
        try:
            with open(path, "r", errors="ignore") as f:
                lines = f.readlines()
                loc = len(lines)
        except Exception:
            loc = 0
        ext = path.suffix or "noext"
        summary["files"].append({"path": rel_path, "loc": loc, "ext": ext})
        summary["total_loc"] += loc
        summary["extensions"].setdefault(ext, 0)
        summary["extensions"][ext] += loc

    return summary
