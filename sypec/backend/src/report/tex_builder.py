"""
Render Jinja → TeX → PDF via latexmk or tectonic (no LaTeX installed in prod!).
Returns the Path to the produced PDF.
"""
from __future__ import annotations
from pathlib import Path
import subprocess
import tempfile
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["tex"]),
    block_start_string=r"(*",
    block_end_string=r"*)",
    variable_start_string=r"{{",
    variable_end_string=r"}}",
)

# latexmk flags: -pdf -silent -output-directory=<out>
LATEXMK_CMD = ["latexmk", "-pdf", "-silent"]


def build_pdf_report(metrics: dict, output_dir: Path) -> Path:
    """Build PDF, copy into output_dir, return Path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        tex_path = tmp / "report.tex"

        template = env.get_template("report.tex.jinja")
        tex_path.write_text(template.render(**metrics), encoding="utf-8")

        subprocess.run(LATEXMK_CMD + [str(tex_path)], cwd=tmp, check=True)
        pdf_src = tmp / "report.pdf"
        pdf_dst = output_dir / f"{metrics['repo_name']}.pdf"
        pdf_dst.write_bytes(pdf_src.read_bytes())
        return pdf_dst
