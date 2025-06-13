FROM python:3.12-slim

ENV POETRY_VERSION=1.8.2
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY . /app

# System deps: git, cloc, latexmk, poppler utils
RUN apt-get update && apt-get install -y git cloc texlive-latex-base latexmk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN poetry config virtualenvs.create false && poetry install --no-dev

CMD ["uvicorn", "backend.src.api:app", "--host", "0.0.0.0", "--port", "80"]
