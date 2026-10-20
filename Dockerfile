# ==============================================================================
# LEXORA Backend Containerfile — Phase 12 Production Hardened
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing bytecode and ensure unbuffered I/O
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -s /bin/bash -m appuser

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create storage, data, and backup directories with non-root ownership
RUN mkdir -p /app/data \
             /app/storage/uploads \
             /app/storage/processed \
             /app/storage/monitoring \
             /app/chroma_db \
             /app/backups \
    && chown -R appuser:appgroup /app

# Copy application code
COPY --chown=appuser:appgroup ./backend /app/backend
COPY --chown=appuser:appgroup ./evaluation /app/evaluation
COPY --chown=appuser:appgroup ./scripts /app/scripts

# Switch to non-root execution
USER appuser

# Expose internal API port
EXPOSE 8000

# Container liveness health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
