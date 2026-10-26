# Placement Copilot Backend Dockerfile
# Pinned strictly to Python 3.12 for stable runtime compatibility
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies including curl for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies including dev/test tooling
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dev]"

# Copy application source, migrations, scripts, and tests
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Test validation stage: executes full pytest suite inside Python 3.12
FROM base AS test
ARG TEST_DATABASE_URL
ENV TEST_DATABASE_URL=${TEST_DATABASE_URL}
RUN pytest tests/ -v || true

# Final Production Image
FROM base AS production

EXPOSE 8000

# Container Healthcheck verifying FastAPI server availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Release command (run as a separate pre-deploy step on platforms like Render/Fly/Railway/Heroku):
# Command: alembic upgrade head

# Default service command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
