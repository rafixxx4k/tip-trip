# Copilot agent instructions — Tip-Trip (trip planner)



Purpose
- You are an automated development agent (GitHub Copilot persona) whose task is to implement and evolve a trip planner app.
- Stack: PostgreSQL (DB) + FastAPI (backend) + React (web) / React Native (mobile).
- Everything must be dockerized and runnable with `docker compose up`.

Agent goals (high level)
- Produce incremental, runnable changes with tests where practical.
- Keep commits small, buildable, and documented.
- Prefer explicit, minimal implementations before optimizations.
- Hardcoded credentials allowed for initial development only; mark TODO to replace with secure auth later.

Standard instructions (how the agent should behave)
- Always provide a short plan for each change.
- Provide or update Dockerfiles and docker-compose to ensure reproducible local environment.
- Add CORS configuration in backend to allow the frontend origin(s).
- For auth: implement a simple login endpoint with hardcoded username/password and return a simple token (e.g., static "dev-token" or a signed JWT if trivial to add). Document clearly.
- When modifying files, create or update minimal necessary files and keep changes isolated.
- Include example fetch/axios snippets for the frontend and for React Native.
- Note required environment variables and defaults; in dev, embed safe defaults and keep secrets out of VCS later.

Architecture overview
- Postgres service: persistent volume, ports open for local debug.
- FastAPI service: connects to Postgres via env vars, exposes HTTP on 8000.
- React web service: dev server on 3000 (or built static assets served by nginx if chosen).
- React Native: instructions to run with Metro bundler; no containerization required for mobile build during early dev (optionally containerize).

NOTE: The canonical backend specification lives in `specification.md`. The section added below is an excerpt of that specification so the Copilot persona can reference API contracts, data models, and endpoint plans while implementing features.

---

## Project specification (excerpt from `specification.md`)

### Trip Planner Application (Backend) Specification

This document outlines the requirements, data models, and RESTful API endpoints for the core backend functionality of the collaborative trip planner application.

#### 1. Core Requirements and Scope

##### 1.1 Non-Authenticated Access (Room-Based)

* Users **do not** need to create accounts or log in.

* Access is granted via a unique, sharable **Room ID (Trip ID)**.

* A user is identified by a temporary `userId` (a UUID or hash) that is generated upon creation or joining a room and stored client-side.

##### 1.2 Core Features

1.  **Scheduling/Calendar:** Collaborative determination of optimal trip dates.

2.  **Expense Splitting:** Tracking, adding, and settling shared expenses.

3.  **AI Chat Agent:** Providing assistance and recommendations for trip planning.

----

#### 2. Data Models (Database Schema) — key fields

We will use four primary collections/tables, linked by `tripId` and `userId`.

- Trip (Room): id, name, organizerUserId, earliestDate, latestDate, availableDaysOfWeek, createdAt
- User (Participant): id, tripId, displayName, socketId
- Availability: id, tripId, userId, date (YYYY-MM-DD), status ('available'|'unavailable'|'maybe')
- Expense: id, tripId, payerId, amount, currency, description, isSplitEqually, debtors (array)

Debtors sub-structure: userId, shareType ('equal'|'percent'|'amount'), value (number)

----

#### 3. REST API Endpoint Plan (prefix: `/api/v1`) — highlights

- POST /trips — create new room (body: name, displayName, earliestDate, latestDate, availableDaysOfWeek) -> { tripId, userId }
- POST /trips/{tripId}/join — join room (body: displayName) -> { userId, tripName, calendarInitialDates }
- GET /trips/{tripId} — trip details + users
- PUT /trips/{tripId} — update trip details

- POST /trips/{tripId}/availability — submit/update availability (body: userId, dates: [{date, status}])
- GET /trips/{tripId}/calendar — returns availability matrix (rows=users, cols=dates)

- POST /trips/{tripId}/expenses — record expense (body: payerId, amount, currency, debtors)
- GET /trips/{tripId}/expenses — list expenses
- GET /trips/{tripId}/settlements — calculate simplified settlements (min transactions)

- POST /trips/{tripId}/chat — AI assistant (body: userId, message) -> { response }

----

#### 4. Integration notes

- AI Chat: call Gemini API (`gemini-2.5-flash-preview-09-2025`) with a system persona describing the trip context.
- Calendar grid logic: generate dates between earliestDate and latestDate matching availableDaysOfWeek; return matrix of user statuses.
- Settlement logic: compute net balances from all expenses and simplify to minimal transactions to settle debts.


FastAPI requirements (dev)
- Use fastapi + uvicorn + asyncpg or sqlalchemy + asyncpg for db
- Add CORS middleware:
  - Allow origins: http://localhost:3000, http://127.0.0.1:3000, plus '*' for early dev if needed
  - Allow credentials, methods, headers
- Simple auth dependency that validates Authorization header == "Bearer dev-token" (or verifies JWT).
- Return clear 401 responses when not authenticated.
- Provide healthcheck endpoint GET /health.

Dockerization guidelines
- Backend Dockerfile:
  - Use python:3.11-slim, install dependencies, copy app, expose 8000, run uvicorn with reload for dev or gunicorn for prod.
- Frontend Dockerfile:
  - Use node:18, install deps, run dev server on 3000; for production build, produce static build.
- Postgres:
  - Use official postgres image, env: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD; mount a volume for data.

Example docker-compose (conceptual)
- services:
  - db: image: postgres:15, volumes, environment (user/pass/db)
  - backend: build ./backend, depends_on: db, ports: "8000:8000", environment: DATABASE_URL=postgresql://user:pass@db:5432/db
  - frontend: build ./frontend (or use create-react-app dev server), ports: "3000:3000"
- Use networks and volumes.

Fetch examples (web)
- Login:
  fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ username: 'admin', password: 'password123' })
  })
  .then(r => r.json())
- Fetch protected resource:
  fetch('http://localhost:8000/trips', {
    headers: { 'Authorization': 'Bearer dev-token' }
  })

Fetch example (React Native)
- Use fetch same as web, but replace origin with backend IP (or use tunnel).
- Ensure CORS handled server-side; mobile generally bypasses browser CORS but backend must accept mobile requests.

CORS guidance
- In FastAPI:
  from fastapi.middleware.cors import CORSMiddleware
  app.add_middleware(CORSMiddleware,
      allow_origins=["http://localhost:3000"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
- For early dev you may set allow_origins=["*"] but note the security risk.

Dev workflow (how to run)
1. Create three folders: ./backend, ./frontend, ./db-scripts (optional).
2. Add Dockerfiles and a docker-compose.yml in project root.
3. Start: docker compose up --build
4. Backend waits for DB: either implement a small wait-for script or use SQLAlchemy with retry logic on startup.
5. Create initial migrations (alembic) later; for earliest dev, run simple CREATE TABLE SQL via an entrypoint script if needed.

Testing and quality
- Add basic unit tests for backend endpoints (pytest + httpx test client).
- Add one integration test to assert login and trips endpoints behavior.
- Linting: use black/ruff/isort for Python, eslint/prettier for frontend.

Security notes / TODOs
- Replace hardcoded credentials with proper user table and password hashing.
- Use real JWT or OAuth for tokens.
- Do not check secrets into VCS.
- Lock down CORS before production.

Useful file snippets to add in early commits (examples)
- backend/app/main.py: FastAPI app + CORS + auth dependency + sample endpoints.
- backend/Dockerfile
- frontend/Dockerfile or simple create-react-app
- docker-compose.yml
- db/init.sql (sample schema)
- README.md with run steps and credentials

Agent operational guideline (how the agent should make requests & changes)
- Each change must include:
  - Short intent summary.
  - Files added/changed.
  - How to run locally to validate.
- Prefer incremental PR-style changes; avoid large one-shot changes.
- When asked to implement an endpoint, include sample curl/fetch and a basic test.
- If a requested change would touch many files and it's unclear which, ask for working set or require `#codebase` to discover files. (If no file list provided when modifying existing project, refuse and prompt to add files.)

Minimal example: login flow (for implementer)
- POST /auth/login checks JSON credentials against hardcoded values.
- If valid → return { access_token: "dev-token", token_type: "bearer" }
- Protected endpoints require header Authorization: Bearer dev-token
- Add tests asserting login success and 401 on failure.

End of instructions — follow these rules when generating code, Docker configs, and docs for the Tip-Trip project.
