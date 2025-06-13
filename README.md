# Sypec

> One-click sustainability audits for GitHub repositories  
> Grades codebases (F–A+++) and predicts kWh at scale.

```bash
# quick start
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.src.api:app --reload
# sypec
