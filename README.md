# Sypec – ChatGPT-Powered Sustainability Auditor
*Last updated: 14 Jun 2025*

---

## 1  What it does
Sypec turns any GitHub repository URL into a sustainability snapshot:

* **JSON** — letter grade, 0-100 score, daily kWh estimates, improvement bullets.  
* **PDF** — LaTeX-generated report (intro, problems, energy graph, totals, recommendations).

All analysis is performed by a single OpenAI call—no heavyweight local static analysis.

---

## 2  Prerequisites
| Requirement      | Version / Notes                                  |
|------------------|--------------------------------------------------|
| Python           | 3.11 or 3.12                                     |
| Git              | any                                              |
| **Tectonic CLI** | `brew install tectonic` (mac) / `apt install tectonic` |
| OpenAI API key   | export as `OPENAI_API_KEY`                        |

---

## 3  Installation
```bash
git clone https://github.com/MiguelIbrahimE/sypec-ml
cd sypec
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt 
```
---

## 4 Running the Server (dev)
```bash
export OPENAI_API_KEY="sk-live-••••"
python -m uvicorn backend.src.api:app \
       --reload --port 8000 \
       --reload-exclude '.venv/*'
```

Swagger UI → http://localhost:8000/docs

## 5 API Usage
```bash
curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"repo_url":"https://github.com/psf/requests"}'
```
