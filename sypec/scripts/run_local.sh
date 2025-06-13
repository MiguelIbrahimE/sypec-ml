#!/usr/bin/env bash
set -euo pipefail
export $(grep -v '^#' .env | xargs)  # load env vars
uvicorn backend.src.api:app --reload
