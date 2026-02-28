# ---------- Build stage ----------
FROM python:3.12-slim AS build

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Download Swagger UI & ReDoc assets ----------
# SPCS ingress CSP blocks external CDN scripts, so we self-host them.
FROM python:3.12-slim AS assets
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /assets
RUN curl -sL -o swagger-ui-bundle.js  "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"  && \
    curl -sL -o swagger-ui.css         "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"         && \
    curl -sL -o redoc.standalone.js    "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"

# ---------- Runtime stage ----------
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from build stage
COPY --from=build /install /usr/local

# Copy self-hosted doc assets
COPY --from=assets /assets/ ./static/

# Copy application code
COPY app/ ./app/

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
