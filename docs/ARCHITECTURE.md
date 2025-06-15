# Sypec — Architecture Overview

## 1  Layer Cake

Layer | Responsibility | Key Modules
----- | -------------- | -----------
API   | HTTP contract, request validation, exception mapping | `backend/src/api.py`
Static Pipeline | Orchestrates all analysers, scoring, PDF build | `static_analyzer/static_pipeline.py`
Analysers | Individual, _pure-Python_ checks (stats, security, energy …) | `static_analyzer/*`
Report | Jinja → LaTeX → PDF via Tectonic | `report/builder.py` + `report/templates`
Utils | Repo clone, git-ignore walker, helpers | `utils/git.py`, `static_analyzer/digest.py`
Infra | Dockerfile, `docker-compose.yml`, GitHub/GitLab snippets | repo root

---

## 2  Data-Flow (Mermaid)

```mermaid
graph TD
    A[POST /analyze] -->|clone_repo| B[/tmp/repo]
    B --> C[Static-Pipeline]
    C --> D[Digest&nbsp;(LOC,&nbsp;files)]
    C --> E[Code&nbsp;Stats]
    C --> F[Security&nbsp;Scan]
    C --> G[Energy&nbsp;Model<br/>(LOC+HW)]
    C --> H[Test&nbsp;Coverage]
    C --> I[PDF&nbsp;Builder]
    C --> J[JSON&nbsp;Summary]

    I -->|Tectonic| P[report.pdf]
    J --> K[(API Response)]

```
Every analyser is stateless and returns a small JSON blob, keeping the pipeline composable.


# 3 Energy Estimation Model

kWh(users) = α · LOC · log₂(users + 1) / 10⁵

