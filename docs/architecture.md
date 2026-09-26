# Outfield Analytics architecture

## Phase 1

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Frontend | Next.js / React, TypeScript, Tailwind CSS | Serve the UI and display API health. |
| Backend | FastAPI, Pydantic, SQLAlchemy | Validate requests, return JSON, and access the database. |
| Database | PostgreSQL 17 | Persist application data; Alembic manages schema migrations. |
| Communication | REST over HTTP, JSON | Connect the frontend to the backend. |

```text
Browser
   |
   v
Next.js / React
   |
   v
FastAPI
   |
   v
PostgreSQL
```

This is a logical layer diagram. Next.js serves the page; React running in the
browser calls FastAPI directly through `frontend/lib/api.ts`. There is currently
no Next.js API proxy. FastAPI permits the configured frontend origin through
CORS. Only the backend connects to PostgreSQL, using SQLAlchemy and the
PostgreSQL protocol rather than REST.

## Current request flow

1. The browser loads the Next.js system-status page.
2. React requests `GET /api/health` at `NEXT_PUBLIC_API_URL`.
3. FastAPI executes `SELECT 1` against PostgreSQL.
4. The API returns HTTP 200 with `{"status":"ok","database":"connected"}`,
   or HTTP 503 with `{"status":"degraded","database":"unavailable"}`.
5. React displays the result and provides a refresh button. If the API cannot be
   reached, it displays Backend **Unavailable** and Database **Unknown**.

Unexpected errors return a generic JSON response. Backend logs record lifecycle
events, database health, request methods, route templates, status, and duration.
Development tracebacks stay in private server logs.

## Local runtime and configuration

Docker Compose runs `frontend`, `backend`, and `db`. The backend waits for the
database health check and runs `alembic upgrade head` before starting FastAPI.
The frontend waits for backend health. PostgreSQL data lives in the named
`postgres_data` volume; normal `docker compose down` preserves it.

Containers reach the API and database using Compose service names. The browser
uses published host addresses. `.env.example` lists the configuration keys;
real values belong in ignored `.env` files. `NEXT_PUBLIC_API_URL` is public and
must never contain credentials. Database credentials stay on the server.

The initial `system_metadata` table provides a small migration and CRUD example.
Baseball ingestion and analytics tables have not been implemented yet.

## Verification

[CI](../.github/workflows/ci.yml) runs frontend install, lint, format checks,
tests, and a production build; backend install, Ruff checks, and pytest run in
a separate job. Unit tests mock health failures and use temporary SQLite
databases for CRUD and migration checks. They do not replace manual PostgreSQL,
Docker networking, browser, and persistence checks.

See [development workflow](development.md) for branches, implementation order,
and the first milestone checklist.

## Planned extensions

- Redis for caching provider responses and computed results.
- MLB public statistics endpoints for current-season data, fetched by FastAPI.
- Retrosheet ingestion into PostgreSQL for historical analysis, with attribution.
- Analytics and ML jobs for features, chronological evaluation, model versions,
  and game predictions.

These are future components. Update this document when they are implemented.
