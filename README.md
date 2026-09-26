# Outfield Analytics

An independent baseball analytics portfolio project combining current-season
and historical data, calculated statistics, and future game predictions.

## Current status

The Phase 1 foundation includes a system-status page, database health checks,
Alembic migrations, Docker Compose, tests, linting, formatting, structured errors,
logging, and GitHub Actions configuration. Hosted CI, browser verification, and
database persistence checks remain pending for the first milestone.

**Stack:** Next.js / React, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy, and
PostgreSQL. The browser communicates with FastAPI through REST/JSON.

Planned features include team and player statistics, projected depth charts,
Redis caching, MLB and Retrosheet data ingestion, and evaluated prediction models.
See [architecture](docs/architecture.md) and [development workflow](docs/development.md).

## Run locally

Start Docker Desktop with its Linux engine enabled, then run from the repository
root in PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Replace the placeholders in .env with your local configuration.
docker compose config --quiet
docker compose up --build
```

Set `DATABASE_URL` to the `db` service using matching `POSTGRES_*` values.
`FRONTEND_URL` is the browser's frontend origin; `NEXT_PUBLIC_API_URL` is its API
origin. Open `FRONTEND_URL` to view the system-status page.

Keep credentials in ignored environment files. Never put secrets in public files
or `NEXT_PUBLIC_*` variables. For frontend work outside Docker, copy
`frontend/.env.example` to `frontend/.env.local` and fill its placeholder.

## Verify

```powershell
docker compose ps
docker compose logs db backend frontend
```

`GET /api/health` returns HTTP 200 when PostgreSQL is connected and HTTP 503 when
it is unavailable. Use **Refresh status** in the UI to check recovery.
`docker compose down` preserves database data; adding `-v` removes the volume.

For code checks, use Node 24 and Python 3.13. Run `npm ci` in `frontend/` and,
with a Python virtual environment activated, `python -m pip install -e ".[test,dev]"`
in `backend/`.

| Directory | Checks |
| --- | --- |
| `frontend/` | `npm run lint`, `npm run format:check`, `npm test`, `npm run build` |
| `backend/` | `ruff check .`, `ruff format --check .`, `python -m pytest --quiet` |

Format with `npm run format` or `ruff format .` in the respective directory.
[CI](.github/workflows/ci.yml) runs checks on every push and pull request;
[development docs](docs/development.md) cover branches and the milestone checklist.

This is a non-commercial project, unaffiliated with MLB or its clubs. Planned
Retrosheet usage will include attribution. No official logos, player photos,
broadcast media, or live game feed are included.
