from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from backend.src.static_analyzer.clone import clone_repo
from backend.src.static_analyzer.static_pipeline import run_static_pipeline

app = FastAPI(title="Sypec – Static Auditor")

class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        repo_path = clone_repo(req.repo_url)
        result = run_static_pipeline(repo_path)
        return {"repo_url": str(req.repo_url), **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
