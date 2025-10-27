#!/bin/sh
set -e

# Run alembic migrations (will use DATABASE_URL from env if present)
# You can skip migrations by setting SKIP_MIGRATIONS=true
if [ "${SKIP_MIGRATIONS}" != "true" ]; then
  if command -v alembic >/dev/null 2>&1; then
    echo "Running alembic migrations..."
    alembic upgrade head || {
      echo "Alembic migration failed" >&2
      exit 1
    }
  else
    echo "alembic command not found; skipping migrations"
  fi
else
  echo "SKIP_MIGRATIONS=true -> skipping alembic migrations"
fi

# Start the application
# In dev mode set DEV=true in docker-compose to enable hot reload
if [ "${DEV}" = "true" ]; then
  echo "Starting uvicorn in dev mode (reload)..."
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/app
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
