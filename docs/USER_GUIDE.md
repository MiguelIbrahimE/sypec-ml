# User Guide – Sypec Auditor

## 1. Overview
Sypec inspects a public Git repository, builds an **energy & quality snapshot**, and returns:
* JSON summary (grade, kWh, warnings)
* A polished PDF report

Typical turnaround: ⩽ 60 s on a laptop / CI runner.

---

## 2. Quick Audit

```bash
curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"repo_url":"https://github.com/psf/requests"}' | jq
```
Field	Meaning
grade	Letter A-F (higher is better)
kwh	Dict: users → daily kWh
bullets	Top issues to fix first
pdf_url	Relative path to full report

# 3. Reading the PDF
Section	What to look for
Scorecard	Overall quality-to-energy ratio
Energy Model	kWh vs user counts; Std-Dev bar
Security Findings	Secrets, CVEs, misconfigs
Code Composition	Language mix & LOC
Smells / Warnings	Actionable refactors

# 4. CI Integration
GitHub Actions
````yaml
name: Audit
on: [push]
jobs:
  sypec-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: false
      - run: |
          RESPONSE=$(curl -s -X POST http://localhost:8000/analyze \
                     -H "Content-Type: application/json" \
                     -d "{\"repo_url\": \"$GITHUB_SERVER_URL/$GITHUB_REPOSITORY\"}")
          echo "$RESPONSE" > audit.json
````
GitLab CI

See docs/snippets/gitlab.yml.

# 5. Troubleshooting
Symptom	Fix
500 Internal Server Error	Check analyzer_debug.log in container
Missing PDF	Ensure tectonic is installed in base image
Energy chart empty	Repo too small (heuristic skipped)

# 6. Support

File issues or discussions on GitHub. 

