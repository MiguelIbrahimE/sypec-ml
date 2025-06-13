"""
ChatGPT-only sustainability analysis.

Workflow
--------
1. Clone the repo (shallow) to a temp dir with GitPython.
2. Build a *digest* of the file tree: "relative/path.ext (loc)".
3. Prompt GPT-4o-mini once.  The model must reply with minified JSON.
4. Parse → dict.  Any model / parse failure returns a safe fallback.
"""
from __future__ import annotations

import json
import os
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, List

import git
import openai
from openai import OpenAIError
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

# ─── Config ──────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"
MAX_FILES_IN_DIGEST = 200  # limit prompt size
MAX_LOC_PER_FILE = 6000    # ignore huge vendored blobs
RETRY = dict(wait=wait_fixed(2), stop=stop_after_attempt(3))

# ─── Helpers ─────────────────────────────────────────────────────────────
def _clone_repo(url: str) -> Path:
    """Shallow-clone into a temp folder; raise RuntimeError on failure."""
    try:
        tmp = tempfile.mkdtemp(prefix="sypec_repo_")
        git.Repo.clone_from(url, tmp, depth=1, no_single_branch=True)
        return Path(tmp)
    except Exception as exc:
        raise RuntimeError(f"git clone failed: {exc}") from exc


def _tree_digest(repo_path: Path) -> str:
    """Return newline-separated 'path (loc)' lines, capped for prompt size."""
    files: List[Path] = sorted(
        p for p in repo_path.rglob("*")
        if p.is_file() and p.stat().st_size < 128_000
    )[:MAX_FILES_IN_DIGEST]

    digest_lines: List[str] = []
    for p in files:
        rel = p.relative_to(repo_path)
        try:
            loc = sum(1 for _ in p.open("r", errors="ignore"))
        except UnicodeDecodeError:
            loc = "binary"
        # skip jumbo files
        if isinstance(loc, int) and loc > MAX_LOC_PER_FILE:
            continue
        digest_lines.append(f"{rel} ({loc})")
    return "\n".join(digest_lines)


def _build_prompt(digest: str) -> str:
    """Generate the single user prompt sent to the model."""
    return textwrap.dedent(
        f"""
        You are a senior sustainability auditor.
        Here is a file list with (lines-of-code) counts:

        ```
        {digest}
        ```

        Estimate:
        • total LOC & language mix
        • CPU/memory hotspots
        • daily kWh for 10,100,1000,10000 active users
        • sustainability score 0-100
        • letter grade F–A+++
        • ≤6 improvement bullets

        Output EXACTLY this minified JSON schema, nothing else:
        {{
          "score": int,
          "grade": str,
          "kwh": {{"10": float,"100": float,"1000": float,"10000": float}},
          "bullets": [str,...]
        }}
        """
    ).strip()


# ─── Core function ───────────────────────────────────────────────────────
@retry(**RETRY, retry=retry_if_exception_type(OpenAIError))
def _call_openai(prompt: str) -> Dict[str, Any]:
    """Call the chat model once and return parsed JSON or raise."""
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Respond JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)  # can raise json.JSONDecodeError


def analyse_repo(url: str) -> Dict[str, Any]:
    """Public façade used by FastAPI route. Always returns a dict."""
    result: Dict[str, Any] = {
        "score": None,
        "grade": "N/A",
        "kwh": {},
        "bullets": [],
    }

    # Step 1: clone
    repo_path = _clone_repo(url)

    # Step 2: digest
    digest = _tree_digest(repo_path)
    prompt = _build_prompt(digest)

    # Step 3: OpenAI call
    if not openai.api_key:
        result.update(
            score=0,
            grade="F",
            bullets=["OPENAI_API_KEY not set; returned fallback."],
        )
        return result

    try:
        ai_json = _call_openai(prompt)
        result.update(ai_json)
    except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
        # Fallback keeps service alive
        result.update(
            score=50,
            grade="C",
            bullets=[
                "Could not parse model output.",
                f"Error: {exc.__class__.__name__}",
                "Add unit tests & CI cache",
            ],
        )
    return result
