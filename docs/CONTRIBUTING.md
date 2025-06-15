# Contributing Guide

## 1. Workflow
1. Fork → feature branch
2. Follow `pre-commit` hooks (`black`, `ruff`, `mypy`)
3. Submit PR, fill template, link issue.

## 2. Commit Style
`<scope>: <subject>` — max 72 chars, present tense.

Example:  
energy: add ARM server profiles


## 3. Code Style
* **Black** (line length 88)
* **Type hints** mandatory for new code
* No external heavy deps without discussion.

## 4. Tests
Run `pytest -q`. New features require unit tests.

## 5. Code of Conduct
Be kind; no harassment; inclusive language; see [`CODE_OF_CONDUCT.md`].
