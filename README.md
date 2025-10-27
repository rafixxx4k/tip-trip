Tip-Trip — Minimal Dockerized Backend (bootstrap)

This repository contains a minimal FastAPI backend and a Docker Compose setup to bootstrap development.

What was added:
- `backend/` — FastAPI app + Dockerfile + requirements
- `docker-compose.yml` — services: `db` (Postgres) and `backend` (FastAPI)
- `db/init.sql` — initial DB init script (optional)

Quick start (requires Docker + Docker Compose):

# build and run
docker compose up --build

# healthcheck
# In another shell:
# curl http://localhost:8000/health

Notes:
- The backend currently uses an in-memory store for trip data (useful for rapid prototyping). The Postgres service is present for future persistence and migrations.
- Backend code lives in `backend/app/main.py` and exposes the following sample routes:
  - GET /health
  - GET /api/v1/trips
  - POST /api/v1/trips
  - POST /api/v1/trips/{tripId}/join
  - GET /api/v1/trips/{tripId}
  - POST /api/v1/trips/{tripId}/expenses
  - GET /api/v1/trips/{tripId}/expenses

Next steps:
- Wire the backend to Postgres (SQLAlchemy/asyncpg) and add migrations.
- Add unit tests (pytest) and CI.
- Implement calendar and settlement algorithms per `specification.md`.
