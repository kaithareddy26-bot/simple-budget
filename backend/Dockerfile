FROM python:3.11-slim AS base

# Consistent, safe Python runtime flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a separate layer so they are cached
# independently of application code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application source — .dockerignore excludes .env*, tests/,
# evidence/, scripts/perf/, __pycache__, and other non-runtime artefacts.
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Run as a non-root user for defence-in-depth
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

# uvicorn workers=1 is safe for a single-container deployment.
# Scale horizontally by running multiple containers behind a load balancer.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]