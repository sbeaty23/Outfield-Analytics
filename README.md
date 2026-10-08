# Outfield Analytics

An independent baseball analytics portfolio project combining current-season
and historical data, calculated statistics, and future game predictions.

## Current status

**Current phase: Phase 2 — Current Baseball Data Integration.**

The application has a replaceable provider boundary, normalized current team,
roster, statistics, standings, schedule, and player contracts, a manual team
reference synchronization command, and simple server-rendered team pages. MLB
responses are translated inside the backend and never exposed directly to
React. See [data sources](docs/data-sources.md) for the current-season policy.

**Stack:** Next.js / React, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy, and
PostgreSQL. Next.js performs server-side requests to FastAPI; FastAPI reaches MLB
only through the provider layer.

Planned later features include projected depth charts, Redis caching, historical
Retrosheet ingestion, and evaluated prediction models.
See [architecture](docs/architecture.md) and [development workflow](docs/development.md).

## Run locally

Start Docker Desktop with its Linux engine enabled, then run from the repository
root in PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Fill the blank settings in .env with your local configuration.
docker compose config --quiet
docker compose up --build
```

Use separate database URLs for the read-only API, migrations, and manual team
synchronization. The matching `POSTGRES_APP_*` and `POSTGRES_SYNC_*` roles are
provisioned idempotently; the bootstrap administrator is never passed to the
long-running API or frontend.
`FRONTEND_URL` is the browser's frontend origin; `NEXT_PUBLIC_API_URL` is its API
origin. `API_INTERNAL_URL` is a separate server-only FastAPI origin reachable
from Next.js (use the backend service hostname in Docker). Bind both published
web services to a local interface with `BACKEND_BIND_HOST` and
`FRONTEND_BIND_HOST`, and list accepted Host header names in the corresponding
allowed-host settings. Open `FRONTEND_URL` to view the system-status page.

Keep credentials in ignored environment files. Never put secrets in public files
or `NEXT_PUBLIC_*` variables. For frontend work outside Docker, copy
`frontend/.env.example` to `frontend/.env.local` and fill the blank connection settings.

## Verify

```powershell
docker compose ps
docker compose logs db backend frontend
docker compose --profile tools run --rm team-sync
```

`GET /api/health` returns HTTP 200 when PostgreSQL is connected and HTTP 503 when
it is unavailable. Use **Refresh status** in the UI to check recovery.
`docker compose down` preserves database data; adding `-v` removes the volume.

For code checks, use Node 24 and Python 3.13. Run `npm ci` in `frontend/` and,
with a Python virtual environment activated, `python -m pip install -e ".[test,dev]"`
in `backend/`.

| Directory | Checks |
| --- | --- |
| `frontend/` | `npm audit --omit=dev --audit-level=high`, `npm run lint`, `npm run format:check`, `npm test`, `npm run build` |
| `backend/` | `pip-audit .`, `ruff check .`, `ruff format --check .`, `python -m pytest --quiet` |

Format with `npm run format` or `ruff format .` in the respective directory.
[CI](.github/workflows/ci.yml) runs checks on every push and pull request;
[development docs](docs/development.md) cover branches and the milestone checklist.

This is a non-commercial project, unaffiliated with MLB or its clubs. Planned
Retrosheet usage will include attribution. No official logos, player photos,
broadcast media, or live game feed are included.

## Phase 2 acceptance

See [Phase 2 verification](docs/phase2-verification.md) for configuration,
team synchronization, API contracts, and offline/live acceptance commands.
