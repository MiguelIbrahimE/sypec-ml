import logging
from pathlib import Path

logger = logging.getLogger(__name__)
def infer_deployment_context(digest: dict) -> str:
    """Return 'desktop' | 'cloud' | 'mobile' …"""
    # … existing heuristics …
    if any("android" in f["path"].lower() for f in digest["files"]):
        return "mobile"
    if any("dockerfile" in f["path"].lower() for f in digest["files"]):
        return "cloud"
    return "desktop"

def infer_project_purpose(repo_path: Path) -> str:
    readme = repo_path / "README.md"
    if not readme.exists():
        logger.warning("README.md not found.")
        return ""

    try:
        content = readme.read_text(encoding="utf-8")
        if len(content.strip()) < 100:
            logger.warning("README.md too short.")
            return ""
        return content.strip()
    except Exception as e:
        logger.error(f"Error reading README.md: {e}")
        return ""
