# ──────────────────────────────────────────────
#  Stage 1: Build dependencies
# ──────────────────────────────────────────────
FROM python:3.11.9-slim AS builder

WORKDIR /app

# Install system dependencies required for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into a dedicated prefix
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ──────────────────────────────────────────────
#  Stage 2: Runtime image
# ──────────────────────────────────────────────
FROM python:3.11.9-slim AS runtime

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Runtime-only system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY ./app ./app

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

# Expose the application port
EXPOSE 8000

# Environment variables (defaults — override at runtime via --env-file or -e)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/')" || exit 1

# Start the FastAPI app with Uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
