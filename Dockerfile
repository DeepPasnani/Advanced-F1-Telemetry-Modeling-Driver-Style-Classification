# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend + serve frontend
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# Run as a non-root user matching the host user (defaults to 1000, the
# typical first-user UID/GID on Linux) so files written into the
# bind-mounted ./cache and ./output volumes aren't root-owned — root-owned
# files there block the host user from writing/deleting them afterward,
# and break this app's own persistence (server/main.py writes
# output/store.json on every session load and analysis).
ARG UID=1000
ARG GID=1000
RUN groupadd -g "$GID" appuser && useradd -u "$UID" -g "$GID" -m appuser \
    && mkdir -p /app/cache /app/output \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Hosts like Railway/Render inject a $PORT env var the app must bind to;
# falls back to 8000 for docker-compose, which doesn't set one.
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
