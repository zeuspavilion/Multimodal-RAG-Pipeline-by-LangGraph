# ============================================================
# Zeus — Multi-stage Dockerfile
# Requires: Docker BuildKit
# Build:    docker build -t zeus-backend .
# Run:      docker run --env-file .env -p 8000:8000 zeus-backend
# ============================================================

# ─── Stage 1: Dependency builder ────────────────────────────
FROM python:3.13-slim AS builder

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy lockfile and pyproject first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-editable

# ─── Stage 2: Model pre-download ────────────────────────────
# Download the embedding model at build time so the container
# never needs internet access at runtime.
FROM python:3.13-slim AS model-downloader

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_HOME=/app/model_cache

# Accept HF_TOKEN as a build arg to authenticate model download
ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN}

RUN python -c "\
from sentence_transformers import SentenceTransformer; \
model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/model_cache'); \
print('[build] Model downloaded successfully.')"

# ─── Stage 3: Production runtime ─────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Install system deps for audio (pydub needs ffmpeg) and PDF (pymupdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment and pre-downloaded model
COPY --from=builder /app/.venv /app/.venv
COPY --from=model-downloader /app/model_cache /app/model_cache

# Copy application source
COPY backend/ ./backend/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tell HuggingFace / sentence-transformers where the cached model is
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_HOME=/app/model_cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache

# Production: no HF mirror needed, model is already local
ENV ENVIRONMENT=production

EXPOSE 8000

# Run with uvicorn (single worker; use Gunicorn + multiple uvicorn workers for production scale)
CMD ["python", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
