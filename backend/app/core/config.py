import os
from typing import List

# Prefer explicit DATABASE_URL, but if it's not provided try to build one from
# the Postgres environment variables set in docker-compose. Fall back to sqlite
# for local development when none are available.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
	pg_user = os.getenv("POSTGRES_USER")
	pg_password = os.getenv("POSTGRES_PASSWORD")
	pg_host = os.getenv("POSTGRES_HOST", "db")
	pg_port = os.getenv("POSTGRES_PORT", "5432")
	pg_db = os.getenv("POSTGRES_DB")
	if pg_user and pg_password and pg_db:
		DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
	else:
		# fallback to a local sqlite file for development
		DATABASE_URL = "sqlite:///./dev.db"

# CORS allowed origins for development
ALLOW_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
