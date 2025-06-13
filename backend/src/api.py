from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from pathlib import Path
from .chatgpt_analyzer import analyse_repo
from .report.builder import build_pdf
from fastapi.responses import FileResponse

app = FastAPI(title="Sypec – ChatGPT-only auditor")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PDF_DIR = DATA_DIR / "reports"

class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        analysis = analyse_repo(str(req.repo_url))
        return {"repo_url": req.repo_url, **analysis}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, detail=str(exc)) from exc

@app.post("/analyze/pdf")
def analyze_pdf(req: AnalyzeRequest):
    try:
        analysis = analyse_repo(str(req.repo_url))
        analysis["repo_name"] = req.repo_url.split("/")[-1]
        pdf = build_pdf(analysis, PDF_DIR)
        return FileResponse(pdf, filename=pdf.name, media_type="application/pdf")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, detail=str(exc)) from exc
