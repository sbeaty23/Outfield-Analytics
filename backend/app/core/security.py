"""Small security middleware suitable for the Phase 2 read-only API."""

import asyncio
from collections import defaultdict, deque
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
        self, app: ASGIApp, *, timeout: float, requests_per_minute: int
    ) -> None:
        self.app = app
        self.timeout = timeout
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_host = client[0] if client else "unknown"
        now = monotonic()
        async with self._lock:
            requests = self._requests[client_host]
            while requests and requests[0] <= now - 60:
                requests.popleft()
            if len(requests) >= self.requests_per_minute:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={"Retry-After": "60"},
                )
                await response(scope, receive, send)
                return
            requests.append(now)

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
