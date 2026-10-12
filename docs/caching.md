# Caching

Outfield Analytics caches normalized current-season Pydantic responses in Redis.
Raw MLB payloads are never cached or returned outside the provider boundary.
Population remains demand-driven: no polling job or bulk team refresh exists.

## Keys and envelopes

Keys begin with `outfield:mlb:v1`, include the configured season, and then name
the resource and relevant identifiers. Statistic group and schedule date range
are part of their keys. The `v1` segment permits a future serialization change
without confusing old and new entries.

Each JSON value contains normalized `data`, `fetched_at`, `fresh_until`, and
`stale_until`. These fields remain internal. Redis expiry is the hard stale
deadline measured from `fetched_at`.

| Resource | Fresh | Hard expiry |
| --- | ---: | ---: |
| Teams, team details, player profiles | 24 hours | 72 hours |
| Active roster | 6 hours | 24 hours |
| Hitting, pitching, and player stats | 30 minutes | 6 hours |
| Fielding stats | 60 minutes | 6 hours |
| Standings | 30 minutes | 6 hours |
| Schedule | 2 hours | 6 hours |

## Read and fallback behavior

A fresh hit returns immediately. A miss or stale value enters a process-local
single flight keyed by the cache key, checks Redis again, and lets one request
refresh from MLB. Concurrent callers share that result even if Redis is down.

A timeout, transport failure, or exhausted temporary upstream response may use a
valid stale value. Not-found and malformed responses never use stale data. Values
past hard expiry are deleted and treated as misses.

Redis connection, timeout, serialization, and schema-validation failures are
sanitized, logged, and treated as cache bypasses. They do not turn a successful
provider response into an API failure.

## Invalidation

The internal cache service supports exact-key deletion and namespace scanning.
The development command below deletes only the Outfield Analytics MLB namespace;
it never flushes the Redis database and has no public HTTP equivalent.

```powershell
python -m app.scripts.clear_cache
```
