# Phase 3 verification

## Automated checks

From `backend/`, run the project test, lint, format, and dependency-audit checks:

```powershell
python -m pytest --quiet
ruff check .
ruff format --check .
pip-audit .
```

From the repository root, verify public configuration and Compose interpolation:

```powershell
python scripts/check_public_config.py
python -m unittest discover -s scripts -p "test_*.py"
docker compose config --quiet
```

Automated provider tests use mock transports and never call MLB. Unit tests cover
cache freshness, stale fallback, disabled/unavailable Redis, deterministic keys,
retry classification and backoff, tiered request limits, request IDs, safe logs,
and concurrent single flight. CI adds a containerized real-Redis round trip with
no host-published Redis port.

## Local acceptance

After filling every blank private `.env` setting, start the stack and inspect
service health:

```powershell
docker compose up --build
docker compose ps
docker compose logs redis backend
```

Verify the following without printing private environment values:

1. Redis and PostgreSQL health checks become healthy and the existing health API
   retains its database-aware contract.
2. A first baseball request logs a miss and provider attempt; an identical second
   request logs a hit and keeps the same public JSON shape.
3. Stop Redis and confirm an uncached provider-backed request still succeeds;
   restart Redis and confirm caching recovers without restarting FastAPI.
4. With a stale test entry and a mocked unavailable provider, confirm stale data
   returns; confirm not-found and malformed failures do not use stale data.
5. Confirm development diagnostics reports dependency status, while a production
   configuration has no diagnostics route.
6. Run the cache-clear command and confirm only the application namespace is
   removed.
7. Review logs for request IDs, route templates, cache status, upstream status,
   and duration, and confirm no URLs, payloads, query values, or credentials are
   present.

Do not tag, commit, push, or claim hosted CI success as part of local verification.
