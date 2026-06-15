# --------------------------------------------------------------------------- #
# Stage 1 — builder: install dependencies into an isolated wheel cache        #
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --no-compile --prefix=/install .

# --------------------------------------------------------------------------- #
# Stage 2 — runtime: minimal image, non-root user, port 8080                  #
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PYTHONPATH=/app/src

WORKDIR /app

# Create non-root user and group
RUN groupadd --system app && useradd --system --gid app --no-create-home app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY src ./src

USER app

EXPOSE 8080

STOPSIGNAL SIGTERM

# Health check via /health/ready — verifies app is truly ready (DOCK-01)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/ready', timeout=4)"

CMD ["uvicorn", "cas_reference_product.app:app", "--host", "0.0.0.0", "--port", "8080"]
