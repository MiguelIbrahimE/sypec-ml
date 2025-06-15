# backend/src/static_analyzer/digest.py
import os
from pathlib import Path
import pathspec
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def load_gitignore(repo_path: Path) -> pathspec.PathSpec:
    ignore_file = repo_path / ".gitignore"
    if ignore_file.exists():
        try:
            with ignore_file.open() as f:
                patterns = f.read().splitlines()
            logger.debug(f"Loaded .gitignore with {len(patterns)} patterns")
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        except Exception as e:
            logger.warning(f"Failed to load .gitignore: {e}")
    else:
        logger.debug("No .gitignore file found")
    return pathspec.PathSpec([])

def get_repo_digest(repo_path: str) -> dict:
    logger.debug(f"Generating repo digest for: {repo_path}")
    repo_path = Path(repo_path)
    if not repo_path.exists():
        logger.error(f"Provided path does not exist: {repo_path}")
        raise FileNotFoundError(f"Invalid repo path: {repo_path}")

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
            logger.debug(f"Ignored by .gitignore: {rel_path}")
            continue
        try:
            with open(path, "r", errors="ignore") as f:
                lines = f.readlines()
                loc = len(lines)
        except Exception as e:
            logger.warning(f"Failed to read {rel_path}: {e}")
            loc = 0
        ext = path.suffix or "noext"
        summary["files"].append({"path": rel_path, "loc": loc, "ext": ext})
        summary["total_loc"] += loc
        summary["extensions"].setdefault(ext, 0)
        summary["extensions"][ext] += loc

    logger.info(f"Digest complete: {len(summary['files'])} files, {summary['total_loc']} LOC")
    return summary
