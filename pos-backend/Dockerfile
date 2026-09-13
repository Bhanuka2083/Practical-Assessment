# -------------------------------------------------------------------
# Stage 1: Build virtual environment using Astral's official uv binary
# -------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (layer caching optimization)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy application source code and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# -------------------------------------------------------------------
# Stage 2: Minimal, secure runtime stage
# -------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Create a dedicated unprivileged user for security
RUN groupadd -g 10001 posgroup && \
    useradd -u 10000 -g posgroup -s /bin/bash -m posuser

WORKDIR /app

# Copy the pre-built virtual environment and application code from builder
COPY --from=builder --chown=posuser:posgroup /app/.venv /app/.venv
COPY --from=builder --chown=posuser:posgroup /app /app

# Switch to the non-root user
USER posuser

# Expose FastAPI default port
EXPOSE 8000

# Health check to ensure the container is responsive
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Production command using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]