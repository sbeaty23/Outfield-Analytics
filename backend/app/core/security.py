"""Security headers, request timeouts, and process-local API rate limits."""

import asyncio
from collections import defaultdict, deque
from collections.abc import Callable
from math import ceil
from time import monotonic

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"referrer-policy": b"no-referrer",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                    b"cache-control": b"no-store",
                    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                }
                existing = {name.lower() for name, _ in headers}
                headers.extend(
                    (name, value)
                    for name, value in security_headers.items()
                    if name not in existing
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


class RequestSecurityMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        timeout: float,
        requests_per_minute: int,
        expensive_requests_per_minute: int = 30,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.app = app
        self.timeout = timeout
        self.requests_per_minute = requests_per_minute
        self.expensive_requests_per_minute = expensive_requests_per_minute
        self._general: dict[str, deque[float]] = defaultdict(deque)
        self._expensive: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._clock = clock
        self._last_prune = 0.0

    @staticmethod
    def _is_expensive(path: str) -> bool:
        return path == "/api/teams" or path.startswith(
            ("/api/teams/", "/api/players/", "/api/standings")
        )

    @staticmethod
    def _expire(requests: deque[float], now: float) -> None:
        while requests and requests[0] <= now - 60:
            requests.popleft()

    def _prune_clients(self, now: float) -> None:
        if now - self._last_prune < 60:
            return
        for buckets in (self._general, self._expensive):
            for client_host, requests in list(buckets.items()):
                self._expire(requests, now)
                if not requests:
                    buckets.pop(client_host, None)
        self._last_prune = now

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path == "/api" or path.startswith("/api/"):
            client = scope.get("client")
            client_host = client[0] if client else "unknown"
            now = self._clock()
            retry_after = 0
            async with self._lock:
                self._prune_clients(now)
                general = self._general[client_host]
                self._expire(general, now)
                expensive = self._expensive[client_host]
                self._expire(expensive, now)

                if len(general) >= self.requests_per_minute:
                    retry_after = max(retry_after, ceil(60 - (now - general[0])))
                is_expensive = self._is_expensive(path)
                if (
                    is_expensive
                    and len(expensive) >= self.expensive_requests_per_minute
                ):
                    retry_after = max(retry_after, ceil(60 - (now - expensive[0])))
                if not retry_after:
                    general.append(now)
                    if is_expensive:
                        expensive.append(now)

            if retry_after:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={"Retry-After": str(max(1, retry_after))},
                )
                await response(scope, receive, send)
                return

        response_started = False

        async def send_with_state(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            async with asyncio.timeout(self.timeout):
                await self.app(scope, receive, send_with_state)
        except TimeoutError:
            if response_started:
                raise
            response = JSONResponse(
                status_code=504, content={"detail": "Request timed out"}
            )
            await response(scope, receive, send)
