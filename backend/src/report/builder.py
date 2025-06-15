from __future__ import annotations

import logging
import subprocess
import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"          # …/report/templates
REPORTS_DIR   = Path("data/reports")                         # docker-volume mount
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────
def _render_latex(ctx: dict) -> str:
    """
    Render `report.tex.jinja` with Jinja-2.
    *Important*: **autoescape=False** – LaTeX must not be HTML-escaped.
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,                # ← fixes “bool is not iterable”
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("report.tex.jinja")
    return template.render(**ctx)


# -------------------------------------------------------------------------
def generate_pdf_report(
        *,
        output_base: Path,
        ctx: dict,
) -> Path:
    """
    Render → compile → return absolute Path to `…/report.pdf`.

    Parameters
    ----------
    output_base : Path
        Folder **without** extension (e.g. data/reports/report_myrepo_20250615_123456)
        will be created; .tex / .pdf live inside it.
    ctx : dict
        Context passed to the Jinja template.
    """
    try:
        output_base.mkdir(parents=True, exist_ok=True)

        tex_file = output_base / "report.tex"
        pdf_file = output_base / "report.pdf"

        log.info("📝  Rendering LaTeX template …")
        tex_file.write_text(_render_latex(ctx), encoding="utf-8")

        log.info("📦  Compiling LaTeX → PDF via latexmk …")
        # latexmk does the “run-until-stable” dance and works inside Alpine/Debian
        subprocess.run(
            ["latexmk", "-pdf", "-quiet", tex_file.name],
            cwd=output_base,
            check=True,
        )

        if not pdf_file.exists():
            raise RuntimeError("latexmk finished but PDF not found")

        log.info("✅  Report generated: %s", pdf_file)
        return pdf_file

    except Exception:
        log.exception("PDF generation failed")
        raise
