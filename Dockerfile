# ──────────────────────────────────────────────
#  Stage 1: Build dependencies
# ──────────────────────────────────────────────
FROM python:3.11.9-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ──────────────────────────────────────────────
#  Stage 2: Runtime image
# ──────────────────────────────────────────────
FROM python:3.11.9-slim AS runtime

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# 👇 IMPORTANT: this is now your app root
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

# 👇 CHANGE: copy contents of app/ directly into /app
COPY ./app .

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/')" || exit 1

# 👇 CHANGE: no more app.main
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port $PORT"]