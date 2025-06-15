import tempfile
from pathlib import Path
import git


def clone_repo(repo_url: str) -> Path:
    tmp_dir = tempfile.mkdtemp(prefix="repo_")
    try:
        git.Repo.clone_from(repo_url, tmp_dir, depth=1)
    except Exception as e:
        raise RuntimeError(f"Failed to clone repo: {e}")
    return Path(tmp_dir)
