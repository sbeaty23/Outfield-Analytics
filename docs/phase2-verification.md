# Phase 2 verification

## Runtime configuration

Fill connection settings in ignored local environment files or deployment
environment variables. All connection fields in examples are intentionally blank.
`MLB_API_BASE_URL` is required and points to the MLB Stats API version-one root.
`MLB_CURRENT_SEASON` is authoritative; set it explicitly and update at rollover.

`NEXT_PUBLIC_API_URL` is the browser-facing FastAPI origin used for health.
`API_INTERNAL_URL` is server-only and must be reachable from Next.js. In Compose,
use the backend service hostname and the configured backend port. Outside Docker,
use the API origin reachable from the local Next.js process. Do not put secrets in
either URL. Never publish the PostgreSQL port or print resolved environment files.
Use distinct credentials for `DATABASE_URL`, `MIGRATION_DATABASE_URL`, and
`SYNC_DATABASE_URL`. The API URL must use `POSTGRES_APP_*`; the one-shot sync URL
must use `POSTGRES_SYNC_*`; only the one-shot migration service receives the
bootstrap administrator URL. Bind public web ports through the local-only bind
settings and configure both allowed-host lists explicitly.

## Contracts and boundaries

Next.js server components use the server-only baseball client. FastAPI routes
delegate to services and the provider normalizes MLB responses. Team detail reads
synchronized identity from PostgreSQL, falling back to the provider when absent.
Database failures roll back and log a sanitized warning before fallback.

| Endpoint | Behavior |
| --- | --- |
| `GET /api/health` | API/database health; never calls MLB |
| `GET /api/teams` | Active MLB teams for the configured season |
| `GET /api/teams/{id}` | Stable team identity |
| `GET /api/teams/{id}/roster` | Current active roster |
| `GET /api/teams/{id}/stats/{group}` | Hitting, pitching, or fielding |
| `GET /api/teams/{id}/schedule` | Optional `start_date` and `end_date` |
| `GET /api/standings` | Normalized AL/NL division standings |
| `GET /api/players/{id}` | Basic player profile |
| `GET /api/players/{id}/stats/{group}` | Hitting or pitching |

Season overrides are rejected with 422. Schedule dates must be ordered, within
the configured calendar year, and at most 31 inclusive days. Defaults run from
today through seven days later, capped at year-end. Outside the configured year,
an explicit start date is required. Provider calls also enforce the date boundary.

Absent optional statistics and last-ten records are null; actual zeros remain
zero. Empty valid statistics return `stats: null`. Innings remain baseball
strings. Invalid required upstream structures return sanitized 502 responses,
timeouts return 504, and missing resources return 404. Next.js renders missing
resources through its not-found boundary and provides a retry view for outages.
Coaching staff remains deferred. No historical ingestion or live feed is included.

## Offline checks

From `backend`, run `python -m pytest --quiet`, `ruff check .`, and
`ruff format --check .`. From `frontend`, run `npm test`, `npm run lint`,
`npm run format:check`, and `npm run build`. From the repository root, run:

```powershell
python scripts/check_public_config.py
python -m unittest discover -s scripts -p "test_*.py"
```

Provider tests use synthetic mock transports. Database tests use isolated SQLite
storage; they do not replace the PostgreSQL acceptance check. Automated tests
must not contact MLB. CI retains frontend/backend checks and configuration checks.
CI also audits runtime Python and npm dependencies. Runtime container builds pin
their base-image digests, install available operating-system security updates,
and omit package managers from the long-running API and frontend images.

## Live checks (explicit, separate from tests)

With Docker Desktop running and local settings populated:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose --profile tools run --rm team-sync
docker compose --profile tools run --rm team-sync
docker compose exec backend python -m app.scripts.check_mlb
```

The one-shot migration service applies migrations before the API starts. The sync
should find 30 clubs; the second run
should insert none and update 30. Verify row count, unique MLB identifiers, and
unchanged internal IDs between runs. Never reset volumes to run acceptance checks.
The live provider command performs a bounded set of reads and reports only outcomes.

Open the configured frontend origin at `/teams`, then follow a team link. Confirm
team and roster content and no MLB requests in browser network activity. Check
`/api/health`, `/docs`, and `/openapi.json` at the configured API origin. Confirm
health reports a connected database and all four API sections are documented.

Report unavailable Docker, PostgreSQL, MLB, or browser checks as pending. Passing
local checks does not establish that hosted CI ran; do not push or commit to verify it.

## Verification record — October 8, 2026

- Passed: 149 backend tests, 35 frontend tests, two configuration-check tests,
  public-configuration scan, Ruff/ESLint, formatting, TypeScript, production build,
  Python dependency audit, and production npm dependency audit.
- Passed: Docker build/start and configuration validation; PostgreSQL and backend healthy.
- Passed: PostgreSQL migration at the teams revision; first sync inserted 30 clubs,
  second sync inserted none and updated 30; IDs remained stable and team detail
  was read from the database without a provider call.
- Passed: bounded live MLB reads for 30 teams, roster, all three team-stat groups,
  six standings divisions, schedule, and applicable hitting/pitching player data.
- Passed: HTTP health, OpenAPI, docs, server-rendered team content, trusted-host
  enforcement, security headers, read-only API database privileges, private
  database DNS, and absence of the Next.js development MCP endpoint.
- Pending: interactive browser and browser network inspection. No browser surface
  was available in the verification session. Server-rendered HTTP checks do not
  replace this final browser check.
- Hosted CI was not run; no commit, push, or tag was created.
