# Sypec – Static Sustainability Auditor
*Last updated: 15 Jun 2025*

---

## 1 What Sypec Does
Give Sypec a **GitHub repo URL** → receive an actionable sustainability dossier:

| Output | Details |
|--------|---------|
| **JSON** (REST) | • Letter grade (F → A+++) & numeric score 0-100<br>• Daily *kWh* projection for 10 → 10 000 users (based on the latest hardware survey)<br>• Key warnings ▸ security, code-smells, low test-coverage …<br>• Link to the full PDF |
| **PDF** (LaTeX) | 8-page report:<br>Intro & Purpose, **Hardware profile** (Steam Survey), **Energy curves**, Resource footprint (RAM / disk), **Security & Smells**, Test-coverage heat-map, Recommendations, Appendix digest |

> **Note** All analysis is offline & deterministic. Set `STATIC_PIPELINE_USE_GPT=true` if you want ChatGPT scoring.

---

## 2 Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Docker + docker-compose** | fastest setup – everything bundled |
| — or — Python ≥ 3.11 | manual venv route |
| Git | any version |
| TeX engine | `latexmk` + `texlive-latex-base` (already in Dockerfile) |
| `OPENAI_API_KEY` | **optional**, only when GPT mode is enabled |

---

## 3 Quick Start

### 3.1 Docker

```bash
git clone https://github.com/MiguelIbrahimE/sypec-ml
cd sypec-ml
docker compose up --build
```
API lives at http://localhost:8000

### 3.2 Virtualenv
````bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.src.api:app --reload --port 8000
````

# 4 Calling the API
````bash
curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"repo_url":"https://github.com/psf/requests"}'
````


Example response (trimmed):
````json
{
"repo_url": "https://github.com/psf/requests",
"intro": "Static analysis of requests",
"purpose": "HTTP client for humans …",
"hardware": {
"desktop": { "cpu": "6-core median", "gpu_share": 32 },
"cloud":   { "instance": "AWS m7g.large", "ram_gb": 8 }
},
"score": 82,
"grade": "B+",
"kwh": { "10": 0.09, "100": 0.8, "1000": 6.7, "10000": 57.0 },
"test_coverage": "≈54 %",
"bullets": [
"No CI badge – coverage uncertain",
"3 high-severity Bandit issues",
"Large binary blobs checked in"
],
"pdf_url": "/static/reports/report_requests_20250615_102233.pdf"
}
````

# 5 Developer Notes
Hardware survey cache → backend/src/static_analyzer/hardware_profiles.py (auto-refreshes weekly; override with STEAM_CACHE_TTL_DAYS).

Extend the pipeline → add a module in static_analyzer/ and chain it in static_pipeline.py.

LaTeX template → edit backend/src/report/templates/report.tex.jinja.

Reports land in data/reports/ (volume-mounted by docker-compose).

Export LOG_LEVEL=DEBUG for verbose container logs.