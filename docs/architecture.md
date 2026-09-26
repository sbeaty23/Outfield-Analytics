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
   or HTTP 503 with `{"detail":"Database unavailable"}`.
5. React displays the result and provides a refresh button. If the API cannot be
   reached, it displays Backend **Unavailable** and Database **Unknown**.

Unexpected errors return a generic JSON response. Backend logs record lifecycle
events, database health, request methods, route templates, status, and duration.
Development tracebacks stay in private server logs.

## API response conventions

Return success payloads directly as JSON with a documented Pydantic response
model; a universal result wrapper is unnecessary. Use HTTP status codes to
indicate success or failure. Health success is HTTP 200 with
`{"status":"ok","database":"connected"}`.

API errors use `{"detail":"Human-readable message"}` with a string `detail`.
Raise FastAPI `HTTPException` for expected failures and document their
`ErrorResponse` schema on the route. Missing routes return 404, unsupported
methods return 405, validation failures return 422, and unexpected failures
return a sanitized 500. Never include credentials or raw exception details in
responses. CORS preflight responses are handled separately by middleware.

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

## Security and Phase 1 scope

Never commit database passwords, API secrets, or real `.env` files. Tracked
`.env.example` files contain blank connection and credential fields only. Git and Docker
ignore local environment files; review staged changes before every commit.

PostgreSQL has no published host port. It shares an internal Compose network
only with the backend; the frontend uses the default network. Use
`docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'`
for local database inspection. Existing `POSTGRES_BIND_HOST` settings are no
longer used.

Future production deployments must expose only the frontend/backend to the
Internet, with PostgreSQL accessible to the backend over a private network.
The current Compose file is a development setup with reload and source mounts,
not a production deployment configuration.

Phase 1 remains Next.js, FastAPI, and PostgreSQL:

- No login, signup, JWT, OAuth, password reset, or sessions; there is no
  user-specific functionality requiring authentication.
- Redis is deferred to Phase 3, when real MLB responses need caching.
- Team, Player, Game, and Roster models are deferred to Phase 2/3 until actual
  MLB responses and Retrosheet requirements have been examined.
- `system_metadata` is the only application table needed to prove migrations
  and database access; Alembic also maintains its migration version table.

## Verification

[CI](../.github/workflows/ci.yml) runs frontend install, lint, format checks,
tests, and a production build; backend install, Ruff checks, and pytest run in
a separate job. Unit tests mock health failures and use temporary SQLite
databases for CRUD and migration checks. They do not replace manual PostgreSQL,
Docker networking, browser, and persistence checks.

See [development workflow](development.md) for branches, implementation order,
and the first milestone checklist.

## Planned extensions

- Redis in Phase 3 for caching provider responses and computed results.
- MLB public statistics endpoints for current-season data, fetched by FastAPI.
- Retrosheet ingestion into PostgreSQL for historical analysis, with attribution.
- Analytics and ML jobs for features, chronological evaluation, model versions,
  and game predictions.

These are future components. Update this document when they are implemented.
