# syntax=docker/dockerfile:1

# ── Stage 1: Build frontend ──────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
# Leverage Docker cache: only reinstall when deps change
COPY frontend/package.json frontend/package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline --no-audit --no-fund || npm install --no-audit --no-fund
COPY frontend ./
# Build-time env: API_BASE empty = same origin (FastAPI serves frontend)
# These are baked at `npm run build` time — BE CAREFUL with secrets.
# VITE_API_KEY is intentionally baked so the browser can auth without extra config.
ARG VITE_API_BASE_URL=""
ARG PRECIS_API_KEY=""
ARG VITE_API_KEY=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV PRECIS_API_KEY=${PRECIS_API_KEY}
ENV VITE_API_KEY=${VITE_API_KEY}
RUN npm run build

# ── Stage 2: Python runtime via conda env `precis` ──────────────────────
# NOTE: This stage is heavy (~2GB) because `environment.yml` includes torch/transformers
# for training. For production API only, you could use `python:3.11-slim` + `pip install -r requirements.txt`
# with a minimal runtime requirements file. We keep conda for parity with local dev.
FROM continuumio/miniconda3:latest

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_ENV=production \
    CONDA_AUTO_UPDATE_CONDA=false

# curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create the `precis` env exactly as you do locally:
#   conda env create -f environment.yml  (or `conda create -n precis python=3.11 && pip install -r requirements.txt`)
COPY environment.yml requirements.txt ./
# Use BuildKit cache for conda pkgs to reduce 4-6min rebuilds
RUN --mount=type=cache,target=/opt/conda/pkgs conda env create -f environment.yml && conda clean -afy

# Make `precis` the default Python for all subsequent layers + runtime
ENV CONDA_DEFAULT_ENV=precis
ENV CONDA_PREFIX=/opt/conda/envs/precis
ENV PATH=/opt/conda/envs/precis/bin:$PATH

# Verify the env (fails fast if not created)
RUN which python && python --version && conda run -n precis python -c "import fastapi, httpx; print('precis env ready')"

# Copy backend flattened to /app so `from config import ...` works with `uvicorn app:app`
COPY backend ./

# Bring built frontend to where app.py expects it: /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# HF Spaces expects 7860, local dev uses 8000 — expose both.
# At runtime HF sets $PORT=7860; locally defaults to 8000 via ENV PORT.
EXPOSE 8000 7860

ENV PORT=8000 \
    OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    DEFAULT_MODEL=phi4-mini:latest \
    AVAILABLE_MODELS=phi4-mini:latest \
    PRECIS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000,http://localhost:7860,https://*.hf.space,https://*.huggingface.co

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || curl -fsS http://localhost:8000/health || curl -fsS http://localhost:7860/health || exit 1

# Uses precis env via PATH; shell form expands $PORT (HF sets 7860, local uses 8000)
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
