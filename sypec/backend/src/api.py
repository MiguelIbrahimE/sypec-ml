"""
FastAPI entry-point. Hit POST /analyze with {"repo_url": "<git url>"}.
Returns JSON payload + stores a PDF report in data/reports/.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from pathlib import Path

from .analyser.main import analyse_repo          # ⬅ note the leading dot
from .report.tex_builder import build_pdf_report # ⬅ same here


app = FastAPI(title="Sypec – Sustainability Analyzer")

PDF_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "reports"
PDF_DIR.mkdir(exist_ok=True, parents=True)


class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl


class AnalyzeResponse(BaseModel):
    repo_url: HttpUrl
    pdf_path: str
    sustainability_score: int  # 0-100


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    try:
        metrics = analyse_repo(str(request.repo_url)) 
        pdf_file = build_pdf_report(metrics, PDF_DIR)
        return AnalyzeResponse(
            repo_url=request.repo_url,
            pdf_path=str(pdf_file.relative_to(PDF_DIR.parent)),
            sustainability_score=metrics["sustainability_score"],
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
