# Outfield Analytics development workflow

## Branches and commits

Keep `main` working and use short-lived feature branches, for example
`feature/frontend-setup`, `feature/backend-setup`, `feature/database`, and
`feature/docker`. A separate `develop`, `staging`, or release branch is not
needed for Phase 1.

```bash
git switch main
git pull --ff-only
git switch -c feature/your-change
# Implement and run the relevant checks.
git add <changed-files>
git diff --cached
git commit -m "feat: describe the working change"
git push -u origin feature/your-change
```

Open a pull request into `main`, wait for both CI jobs to pass, review the diff,
and merge. Keep credentials and local environment files out of commits. Commit
each working increment; do not recreate completed stages just to manufacture
their suggested commit sequence.

## CI

The [CI workflow](../.github/workflows/ci.yml) runs on every push and pull request.
It uses Node 24 and Python 3.13 to match the Docker runtimes. It has read-only
repository permissions and performs no deployment.

| Job | Checks in order |
| --- | --- |
| Frontend | `npm ci`, `npm run lint`, `npm run format:check`, `npm test`, `npm run build` |
| Backend | `python -m pip install -e ".[test,dev]"`, `ruff check .`, `ruff format --check .`, `python -m pytest --quiet` |

Run these commands from `frontend/` or `backend/` respectively. Next.js builds
also check TypeScript. CI uses a public test API origin and backend test fixtures;
it requires no repository secrets or live database. The first actual GitHub run
can be confirmed only after the workflow is pushed.

The setup follows the official [Node action](https://github.com/actions/setup-node)
and [Python action](https://github.com/actions/setup-python) documentation.

## Phase 1 implementation order

The existing code covers steps 1–10. Keep this order when rebuilding the stack
or diagnosing a fresh setup; verify each layer before adding the next.

| Step | Increment | Verification before committing |
| --- | --- | --- |
| 1 | Repository, folders, README, ignore rules | Inspect tracked files for secrets. |
| 2 | Next.js, TypeScript, Tailwind, homepage | Open `FRONTEND_URL` from your local environment. |
| 3 | FastAPI and `/api/health` | Request `NEXT_PUBLIC_API_URL` plus `/api/health`. |
| 4 | `frontend/lib/api.ts` | Confirm the browser receives the backend response. |
| 5 | PostgreSQL and SQLAlchemy session | Confirm a database connection. |
| 6 | Alembic and initial table | Run `alembic upgrade head` and inspect `system_metadata`. |
| 7 | Database-aware health endpoint | Check healthy and database-unavailable JSON responses. |
| 8 | Docker database and backend | Confirm FastAPI reaches the Compose database service. |
| 9 | Docker frontend | Run `docker compose up --build` and check the complete UI flow. |
| 10 | Tests, linting, formatting | Pass pytest, Vitest, ESLint, Ruff, and formatting checks. |
| 11 | GitHub Actions | Push the workflow and confirm both jobs are green. |
| 12 | Documentation and milestone | Review README, architecture, environment examples, and tag the verified commit. |

## First milestone: v0.1.0

For manual recovery checks, open the system-status page, stop the backend with
`docker compose stop backend`, and refresh to confirm it shows unavailable.
Run `docker compose start backend` and refresh to confirm recovery. Repeat with
`db` to check the degraded database state and recovery. PostgreSQL initialization
variables only apply to a new data volume; changing them does not update an
existing database.

The tag identifies the initial foundation, not a production release. A local tag
can record the code milestone while hosted CI and manual checks remain pending.
Before publishing it, after the feature branch is merged and GitHub CI passes on
`main`, run the manual browser
health/recovery checks above and confirm database data persists after
container recreation. Use `docker compose down` without `-v` to preserve data.

If no local milestone tag exists yet, tag the verified commit, then publish it:

```bash
git switch main
git pull --ff-only
git tag -a v0.1.0 -m "Outfield Analytics Phase 1 foundation"
git push origin v0.1.0
```

If the tag already exists locally, verify that its commit is the intended
milestone and push that tag without recreating it. Do not move an existing
milestone tag. Record any remaining checks before claiming the milestone is
fully verified.
