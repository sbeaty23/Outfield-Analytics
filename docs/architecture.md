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

Docker Compose runs `frontend`, `backend`, and `db`, plus short-lived role
provisioning and migration services. The read-only backend starts only after
role provisioning and `alembic upgrade head` complete. Manual team synchronization
runs in its own profile with a non-superuser write role. The frontend waits for
backend health. PostgreSQL data lives in the named
`postgres_data` volume; normal `docker compose down` preserves it.

The frontend and backend share the edge network; only the backend, database, and
short-lived database jobs join the private data network. Published web ports bind
through explicit local host settings. Runtime containers use non-root users,
read-only filesystems, dropped capabilities, resource limits, and immutable
production images. `.env.example` lists configuration keys; real values belong
in ignored `.env` files. `NEXT_PUBLIC_API_URL` is public and must never contain
credentials.

The initial `system_metadata` table provides a small migration and CRUD example.
Baseball ingestion and analytics tables have not been implemented yet.

## Phase 2 foundation

The first baseball endpoints follow this boundary:

```text
FastAPI team router -> TeamService -> BaseballDataProvider -> MLBProvider -> MLB Stats API
```

`app/providers/base.py` defines the asynchronous provider contract.
`TeamService` depends on that contract; routes obtain the service through FastAPI
dependencies. The composition root in `main.py` creates one shared asynchronous
HTTP client per application lifespan and closes it on shutdown. Only
`app/providers/mlb.py` knows MLB URLs, query names, and response structures. It
validates upstream responses and returns the application's Pydantic schemas.
Replacing the provider dependency requires no route changes.

Implemented endpoints:

| Endpoint | Result |
| --- | --- |
| `GET /api/teams` | Active MLB teams, with configured season metadata. |
| `GET /api/teams/{team_id}` | One active MLB team. |
| `GET /api/teams/{team_id}/roster` | Current active roster, with team and season metadata. |

All baseball routes reject override query parameters `season`, `date`, `sportId`, and
`rosterType`, with HTTP 422. Positive numeric team IDs are required. The provider
always supplies `settings.mlb_current_season`; its public methods accept no
season argument. Roster, statistics, and schedule requests first check that the ID identifies an active
MLB team, since upstream also accepts minor-league IDs. No historical MLB request
path is exposed. Future historical routing belongs in the service layer with a
separate historical provider policy.

Configuration lives in `Settings`: `MLB_API_BASE_URL`, `MLB_SPORT_ID` (restricted
to `1`), `MLB_CURRENT_SEASON`, and `MLB_REQUEST_TIMEOUT_SECONDS` (greater than zero,
at most 60). Without an explicit season, the default is the current UTC year at
startup. Set the season explicitly in deployment and review it at rollover;
restart the backend after changing it. No public request can change this setting.

Missing or out-of-scope resources return 404. Provider timeouts return 504;
network errors, upstream rate limits/server errors, and malformed responses
return 502. Responses never expose upstream bodies. An empty roster is valid;
a missing or malformed roster field is an upstream error. There are no retries,
caches, automatic syncs, or startup network requests.

Phase 2 includes PostgreSQL team reference persistence and transactional manual
sync, team/player statistics, player profiles, standings, and schedules. Next.js
server components fetch normalized baseball data through a server-only client
using `API_INTERNAL_URL`. The browser health panel continues to use the public
API origin. No browser baseball requests go directly to MLB.

Schedule policy is enforced in services and at the provider boundary: dates must
fall in the configured calendar year and cover at most 31 inclusive days. Optional
missing statistics and empty statistical splits remain null, not invented zeros.
See [Phase 2 verification](phase2-verification.md) for the full endpoint table,
configuration, sync commands, and live acceptance results.

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
- Retrosheet ingestion into PostgreSQL for historical analysis, with attribution.
- Analytics and ML jobs for features, chronological evaluation, model versions,
  and game predictions.

These are future components. Update this document when they are implemented.
