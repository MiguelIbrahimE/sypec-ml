# backend/src/static_analyzer/clone.py
from pathlib import Path
import tempfile
import git

def clone_repo(url: str) -> Path:
    tmp = tempfile.mkdtemp(prefix="sypec_repo_")
    git.Repo.clone_from(url, tmp, depth=1)
    return Path(tmp)
