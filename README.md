# Sypec — Sustainability Auditor for Software Repos
*Last updated: 15 Jun 2025*

---

## 1 What Sypec delivers ⚡️🌍

| Output            | Format / Route     | What you get                                                                 |
|-------------------|--------------------|------------------------------------------------------------------------------|
| **Snapshot JSON** | `POST /analyze`    | Grade (A–F) • score (0-100) • kWh table • top warnings                       |
| **Full PDF**      | LaTeX → PDF file   | Exec summary • energy model • security & quality findings • recommendations |
| **Docs bundle**   | Markdown files     | User guide • API reference • FAQ                                             |

All analysis runs inside a single container in seconds — perfect for CI gates.

---

## 2 Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Python** 3.11 / 3.12 | Any CPython distro |
| **Git** | Any recent version |
| **Tectonic CLI** | `brew install tectonic` / `apt install tectonic` |
| OpenAI key | `export OPENAI_API_KEY=sk-live-•••` |

---

## 3 Installation

```bash
git clone https://github.com/MiguelIbrahimE/sypec-ml
cd sypec-ml
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
```
# 4 Quick Start (Dev server)
````bash
uvicorn backend.src.api:app --reload --port 8000
# Swagger UI → http://localhost:8000/docs
````
# 5 User Manual 📖

See docs/USER_GUIDE.md for:

    End-to-end walkthrough of a typical audit

    How to read scores & grades

    Integrating Sypec with GitHub Actions / GitLab CI

    Exporting extra artefacts (CSV, dashboards, badges)

# 6 FAQ ❔

Why LaTeX? Portable, high-quality long-term archive.
Which languages are scanned? Any text source; first-class support for Python, TypeScript, Go, Rust & Dockerfiles.

More answers in docs/FAQ.md.

# 7 Code & API Docs 🛠️

    docs/ARCHITECTURE.md — folder layout, data flow, extensibility hooks.

    docs/API_REFERENCE.md — every endpoint, schema & example payloads.
# 8 Contributing

PRs welcome! Please read CONTRIBUTING.md (style guide, commit rules) and open an issue first for major changes.
