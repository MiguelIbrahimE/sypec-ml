from __future__ import annotations
import subprocess, tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPL_DIR = Path(__file__).parent / "templates"
env = Environment(
    loader=FileSystemLoader(str(TEMPL_DIR)),
    autoescape=select_autoescape(["tex"]),
)

def _make_plot(kwh: dict[str, float]) -> Path:
    users = [int(u) for u in kwh]
    vals  = [kwh[str(u)] for u in users]

    fig, ax = plt.subplots()
    ax.bar([str(u) for u in users], vals)
    ax.set_xlabel("Concurrent users")
    ax.set_ylabel("Daily kWh")
    fig.tight_layout()

    tmpdir = Path(tempfile.mkdtemp())
    img = tmpdir / "energy.png"
    fig.savefig(img, dpi=180)
    plt.close(fig)
    return img

def _run_tectonic(tex: Path, outdir: Path):
    cmd = ["tectonic", "--outdir", str(outdir), "--print", "0", str(tex)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Tectonic failed:\n{proc.stderr}")

def build_pdf(data: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    img = _make_plot(data["kwh"])
    tex_code = env.get_template("report.tex.jinja").render(**data, energy_graph=str(img))

    tmpdir = Path(tempfile.mkdtemp())
    tex = tmpdir / "report.tex"
    tex.write_text(tex_code, encoding="utf-8")

    _run_tectonic(tex, tmpdir)

    pdf = tmpdir / "report.pdf"
    final = out_dir / f"{data['repo_name']}.pdf"
    final.write_bytes(pdf.read_bytes())
    return final
