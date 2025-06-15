# ---------- base ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# system deps: git + minimal TeX tool-chain for PDF
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git curl ca-certificates build-essential \
        latexmk texlive-latex-base texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# ---------- python deps ----------
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r /app/backend/requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

# ---------- project source ----------
COPY backend /app/backend
RUN mkdir -p /app/data/reports

EXPOSE 8000
CMD ["uvicorn", "backend.src.api:app", "--host", "0.0.0.0", "--port", "8000"]
