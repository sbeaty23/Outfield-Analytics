"""Small application logger; never log request bodies, headers, or query strings."""

import logging
from time import perf_counter

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import handle_unexpected_error

logger = logging.getLogger("app")


def configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
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
        response_started = False
        logger.info("Request received method=%s", scope["method"])

        async def send_with_status(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        except Exception as error:
            response = await handle_unexpected_error(Request(scope), error)
            if response_started:
                raise
            await response(scope, receive, send_with_status)
        finally:
            # Route templates exclude user-supplied path parameters.
            route = getattr(scope.get("route"), "path", "unmatched")
            logger.info(
                "Request completed method=%s route=%s status=%s duration_ms=%.1f",
                scope["method"],
                route,
                status_code,
                (perf_counter() - started) * 1000,
            )
