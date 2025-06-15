import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import subprocess
import logging
import uuid

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_report(context: dict, repo_name: str) -> str:
    try:
        logger.info("Rendering LaTeX report...")
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template("report.tex.jinja")

        tex_content = template.render(context)
        safe_name = repo_name.replace("/", "_").replace(":", "_")
        report_id = f"{safe_name}_{uuid.uuid4().hex[:8]}"
        report_path = REPORTS_DIR / report_id
        report_path.mkdir(parents=True, exist_ok=True)

        tex_file = report_path / "report.tex"
        pdf_file = report_path / "report.pdf"

        tex_file.write_text(tex_content)

        logger.debug(f"Compiling LaTeX file at: {tex_file}")
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file.name],
            cwd=report_path,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if not pdf_file.exists():
            raise RuntimeError("PDF was not generated.")

        logger.info(f"Report successfully generated at: {pdf_file}")
        return str(pdf_file)
    except Exception as e:
        logger.exception("Failed to generate PDF report.")
        raise
