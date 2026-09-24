# Outfield Analytics

An independent baseball analytics project. The goal is to combine current-season information with historical data, calculate useful statistics, and eventually predict upcoming games. This is a portfolio project under active development, not a production service.

## What the app will do

- **Teams:** Records, standings, run differential, recent form, scoring trends, rosters, coaches, and schedules.
- **Players and stats:** Player pages and sortable batting, pitching, and fielding tables. The app will calculate metrics such as AVG, OBP, SLG, OPS, ERA, WHIP, and rolling trends.
- **Depth charts:** Project likely starters from recent starts, appearances, and positional usage. These will be labeled as projections, not official depth charts.
- **Game predictions:** Estimate each team's win probability using recent form, run differential, offense, pitching, home field, rest, and available starter information. Logistic regression is the baseline; tree-based models may follow.
- **Model Lab:** Show backtest results, calibration, accuracy, ROC-AUC, Brier score, and log loss. Training and evaluation will use chronological splits.

The app will do more than display data from another API. It will normalize source data, calculate its own metrics, and explain how its projections perform.

## Data and architecture

Current-season rosters, stats, standings, coaching staff, and schedules will come from narrow requests to MLB's public statistics endpoints. The backend will request and cache that data; the browser will not call the provider directly. Historical games and statistics will primarily come from Retrosheet, processed into PostgreSQL for analysis and model training. The deployed app will include Retrosheet attribution.

```text
Browser → Next.js / React → FastAPI → PostgreSQL
                           ├──────→ MLB current-season data (planned)
                           ├──────→ Redis cache (planned)
                           └──────→ analytics and ML (planned)
```

The frontend uses Next.js, React, TypeScript, and Tailwind CSS. The backend uses Python, FastAPI, Pydantic, SQLAlchemy, and Alembic. PostgreSQL stores application and historical data. The test stack is pytest, Vitest, and React Testing Library. Later work may use pandas, NumPy, scikit-learn, XGBoost, and Recharts. Planned deployment is Vercel for the frontend and Railway or Render for the backend, with hosted PostgreSQL and Redis.

This is a non-commercial, independent project. It will not use MLB or team logos, official player photos, broadcast media, MLB articles, a live game feed, or bulk redistribution of MLB data. It is not affiliated with MLB or any club.

## Run locally

Start Docker Desktop with its Linux engine enabled. From the repository root in PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Fill the placeholders in .env with your local ports, bind addresses, and credentials.
docker compose config --quiet
docker compose up --build

# Later starts:
docker compose up
```

Keep real values in the ignored `.env`. Set `DATABASE_URL` to use the `db` service and the same database, user, password, and port as the PostgreSQL variables. Set `FRONTEND_URL` to the browser's frontend origin and `NEXT_PUBLIC_API_URL` to its backend origin. For frontend work outside Docker, create `frontend/.env.local` from `frontend/.env.example` and fill its placeholder. PostgreSQL initialization variables apply when a new data volume is created; changing them does not update an existing database.

Open `FRONTEND_URL` to see the system-status page. React calls `GET /api/health` through `NEXT_PUBLIC_API_URL` and displays the result:

```text
PostgreSQL healthy → migrations run → FastAPI healthy → frontend starts
Browser → health request → FastAPI runs SELECT 1 → React shows status
```

An HTTP `200` means the backend and database are connected. An HTTP `503` means the backend is reachable but PostgreSQL is unavailable. If the API cannot be reached, the page shows Backend **Unavailable** and Database **Unknown**. Use **Refresh status** to check again. Compose waits for healthy dependencies at startup; it does not automatically restart a service that later becomes unhealthy.

Inside Compose, the backend reaches PostgreSQL at `db:<postgres-port>`, and containers reach FastAPI at `backend:<backend-port>`. Your browser uses the published host ports. `localhost` inside a container refers to that container. Set `POSTGRES_BIND_HOST` to a loopback address if local database tools should be the only host clients.

## Check the stack

```powershell
docker compose ps
docker compose logs db backend frontend
```

Open `NEXT_PUBLIC_API_URL` plus `/api/health`. A healthy response is `{"status":"ok","database":"connected"}`, and the page should show Frontend **Online**, Backend **Connected**, and Database **Connected**. To check recovery, stop the backend with `docker compose stop backend`, refresh the page, then run `docker compose start backend` and refresh again. Stop and restart `db` the same way to check the degraded database state.

`docker compose down` keeps the named PostgreSQL volume. Avoid `down -v` unless you intend to remove stored data.

Run the code checks from their respective directories:

| Directory | Commands |
| --- | --- |
| `backend/` | `python -m pytest --quiet` |
| `frontend/` | `npm test`, `npm run lint`, `npx tsc --noEmit` |

## Roadmap and current status

1. **Foundation:** Next.js, FastAPI, PostgreSQL, migrations, Compose, a live status page, and basic tests.
2. **Current data:** Teams, rosters, stats, schedules, standings, and normalization.
3. **Reliability:** Redis caching, rate limits, error handling, and cached fallback data.
4. **First full UI:** Team selection, overview, roster, stats, and schedule. This is the first planned public release.
5. **Historical data:** Retrosheet ingestion and PostgreSQL datasets.
6. **Analytics:** Rolling metrics, player pages, trends, charts, and projected depth charts.
7. **Prediction model:** Features, training data, a logistic regression baseline, and a prediction service.
8. **Evaluation:** Chronological backtests, calibration, model comparisons, and Model Lab.
9. **Upcoming games:** Combine the historical model with current-season inputs.
10. **Production polish:** CI/CD, monitoring, logging, documentation, and performance.

Phase 1 is in progress. The app, database, migrations, Compose startup, health query, container networking, CORS, and backend outage/recovery have been checked locally. Backend and frontend tests pass. CI, visual browser confirmation, and database persistence after container recreation are still pending. Features and model choices may change as the project develops.
