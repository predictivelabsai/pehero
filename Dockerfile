# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps for psycopg binary, pgvector, fastembed, reportlab (image libs).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Deps layer — copy only requirements first so deps are cached across code edits.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Pre-download the fastembed ONNX model so cold-start in prod doesn't fetch
# over the network (speeds up the first RAG call to ~200ms).
RUN python - <<'PY'
from fastembed import TextEmbedding
TextEmbedding("BAAI/bge-small-en-v1.5")
print("fastembed model cached")
PY

# App code
COPY . .

EXPOSE 5057

# Coolify health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:5057/app/_debug/ping || exit 1

CMD ["python", "main.py"]
