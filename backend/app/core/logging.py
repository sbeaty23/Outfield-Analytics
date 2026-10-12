"""Small application logger; never log request bodies, headers, or query strings."""

import logging
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import handle_unexpected_error

logger = logging.getLogger("app")
request_id_context: ContextVar[str] = ContextVar("request_id", default="none")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


def configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s "
                "request_id=%(request_id)s %(message)s"
            )
        )
        handler.addFilter(RequestIdFilter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = perf_counter()
        status_code = 500
        request_id = uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_context.set(request_id)
        logger.info("Request received method=%s event=request_started", scope["method"])

        async def send_with_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                if b"x-request-id" not in {name.lower() for name, _ in headers}:
                    headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        finally:
            # Route templates exclude user-supplied path parameters.
            route = getattr(scope.get("route"), "path", "unmatched")
            logger.info(
                "Request completed event=request_completed method=%s route=%s "
                "status=%s status_code=%s duration_ms=%.1f",
                scope["method"],
                route,
                status_code,
                status_code,
                (perf_counter() - started) * 1000,
            )
            request_id_context.reset(token)


class RequestErrorMiddleware:
    """Convert uncaught inner-stack failures before CORS decorates the response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_with_state(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_with_state)
        except Exception as error:
            if response_started:
                raise
            response = await handle_unexpected_error(Request(scope), error)
            await response(scope, receive, send_with_state)
