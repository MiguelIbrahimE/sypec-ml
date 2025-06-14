"""
ChatGPT-only sustainability analysis (V2).

Workflow
--------
1. Shallow-clone repo with GitPython.
2. Read .gitignore and skip ignored paths.
3. Build digest "path (loc) [sha6]".
4. Single GPT-4o-mini call → minified JSON.
5. Parse → dict. Fallback JSON if anything fails.
"""
from __future__ import annotations

import json, os, tempfile, textwrap, hashlib, mimetypes
from pathlib import Path
from typing import Dict, Any, List

import git
import openai
from openai import OpenAIError
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
import pathspec

# ─── Config ──────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"
MAX_FILES = 200
MAX_LOC = 6000
RETRY = dict(wait=wait_fixed(2), stop=stop_after_attempt(3))

# ─── Helpers ─────────────────────────────────────────────────────────────
def _clone_repo(url: str) -> Path:
    tmp = tempfile.mkdtemp(prefix="sypec_repo_")
    git.Repo.clone_from(url, tmp, depth=1, no_single_branch=True)
    return Path(tmp)

def _gitignore_spec(repo: Path):
    fp = repo / ".gitignore"
    if not fp.exists():
        return pathspec.PathSpec.from_lines("gitwildmatch", [])
    return pathspec.PathSpec.from_lines("gitwildmatch", fp.read_text().splitlines())

def _tree_digest(repo: Path) -> str:
    ignore = _gitignore_spec(repo)
    files: List[Path] = []
    for p in sorted(repo.rglob("*")):
        rel = p.relative_to(repo)
        if p.is_file() and not ignore.match_file(rel.as_posix()):
            files.append(p)
    files = files[:MAX_FILES]

    lines: List[str] = []
    for p in files:
        rel = p.relative_to(repo)
        if mimetypes.guess_type(p)[0] and mimetypes.guess_type(p)[0].startswith("image"):
            continue
        try:
            loc = sum(1 for _ in p.open("r", errors="ignore"))
        except UnicodeDecodeError:
            loc = "binary"
        if isinstance(loc, int) and loc > MAX_LOC:
            continue
        sha = hashlib.md5(rel.as_posix().encode()).hexdigest()[:6]
        lines.append(f"{rel} ({loc}) [{sha}]")
    return "\n".join(lines)

# grading helper ----------------------------------------------------------
_GRADES = "F D C B A A+ A++ A+++".split()
def _grade(score: int) -> str:
    idx = min(max(score, 0) // 15, len(_GRADES) - 1)
    return _GRADES[idx]

def _build_prompt(digest: str) -> str:
    return textwrap.dedent(f"""
    You are a rigorous software-sustainability auditor.

    The digest already excludes .gitignored files.

    ```txt
    {digest}
    ```

    Evaluate:
    • language mix & doc coverage (README, docs/, FAQs)
    • Dockerfile image size & RAM hints
    • CI/tests presence, secrets exposure, auth flows
    • Scalability & absence of spaghetti code
    • Energy per language (Python>JS>Go>Rust>…)
    • Estimate daily kWh for 10,100,1k,10k users: median & ±30 % dev
    • kWh for this report ≈ 0.015
    • Output 1-line intro + ≤6 bullets, score 0-100, grade F-A+++.

    Return STRICT minified JSON:
    {{
      "intro": str,
      "score": int,
      "grade": str,
      "kwh": {{"10":[float,float],"100":[...],"1000":[...],"10000":[...]}},
      "bullets": [str,...]
    }}
    """).strip()

# ─── OpenAI call ─────────────────────────────────────────────────────────
@retry(**RETRY, retry=retry_if_exception_type(OpenAIError))
def _ask_openai(prompt: str) -> Dict[str, Any]:
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Respond JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=400,
    )
    return json.loads(resp.choices[0].message.content.strip())

# ─── Main façade ─────────────────────────────────────────────────────────
def analyse_repo(url: str) -> Dict[str, Any]:
    repo = _clone_repo(url)
    digest = _tree_digest(repo)
    prompt = _build_prompt(digest)

    fallback = {
        "intro": "Sustainability snapshot unavailable.",
        "score": 50,
        "grade": "C",
        "kwh": {"10":[0.4,0.1],"100":[1.0,0.3],"1000":[10,3],"10000":[80,24]},
        "bullets": ["Fallback response; check OpenAI key/config."],
    }

    if not openai.api_key:
        return fallback

    try:
        ai = _ask_openai(prompt)
        # ensure grade present
        ai.setdefault("grade", _grade(ai.get("score", 0)))
        return ai
    except Exception:
        return fallback
