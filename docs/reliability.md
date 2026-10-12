# Reliability and request control

## MLB transport

Every MLB request has a configured timeout, response-size bound, and concurrency
limit. The provider makes at most three attempts. Timeout and transport failures,
plus upstream 429, 502, 503, and 504 responses, retry after bounded exponential
delays. HTTP 404, other client errors, HTTP 500, oversized bodies, invalid JSON,
and schema failures do not retry.

Terminal exceptions are normalized as not-found, timeout, temporarily
unavailable, or general provider errors. Responses and logs never contain raw
upstream bodies or exception messages.

## Incoming limits

The FastAPI process enforces a sliding one-minute budget per direct peer:

- 100 requests across `/api`.
- 30 requests across team, player, and standings resources.

Expensive requests consume both budgets. Rejections return HTTP 429, a
`Retry-After` header, and a stable JSON error. Counters and single-flight state
are process-local. A multi-worker deployment needs a distributed design before
claiming global enforcement.

Forwarded client-address headers are ignored. When deploying behind a proxy,
configure and audit the trusted proxy boundary before using forwarded identity;
otherwise clients could forge it. Server-rendered Next.js calls may share the
frontend container's direct-peer budget, which is acceptable for the current
single-instance portfolio deployment and must be revisited before scaling.

## Observability and dependency behavior

Every request receives a generated `X-Request-ID`. Log records correlate it with
route templates, status, duration, cache decisions, provider attempts, safe
numeric identifiers, upstream status, and latency. Query strings, request bodies,
headers, cache payloads, connection URLs, and exception messages are excluded.

`GET /api/health` retains its database-aware 200/503 contract and never calls
MLB. Development/test `GET /api/diagnostics` reports database and Redis status
and whether the provider is configured, also without calling MLB. Redis failure
does not prevent application startup or successful provider-backed responses.
