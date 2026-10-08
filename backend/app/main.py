import logging
from contextlib import asynccontextmanager

import httpx2 as httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api import health, players, standings, teams
from app.core.config import APP_TITLE, APP_VERSION, settings
from app.core.errors import (
    handle_provider_error,
    handle_unexpected_error,
    handle_validation_error,
)
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.core.security import RequestSecurityMiddleware, SecurityHeadersMiddleware
from app.database.session import engine
from app.providers.exceptions import ProviderError
from app.providers.mlb import MLBProvider

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logging()
    logger.info("Outfield Analytics application started")
    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            trust_env=False,
            limits=httpx.Limits(max_connections=16, max_keepalive_connections=8),
        ) as client:
            application.state.baseball_provider = MLBProvider(client, settings)
            yield
    finally:
        engine.dispose()
        logger.info("Outfield Analytics application stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        lifespan=lifespan,
        responses={
            422: {"model": ErrorResponse, "description": "Request validation failed."},
            500: {"model": ErrorResponse, "description": "Internal server error."},
        },
    )

    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )
    application.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts
    )
    application.add_middleware(
        RequestSecurityMiddleware,
        timeout=settings.request_timeout_seconds,
        requests_per_minute=settings.request_rate_limit_per_minute,
    )
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_exception_handler(Exception, handle_unexpected_error)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(ProviderError, handle_provider_error)
    application.include_router(health.router, prefix="/api")
    application.include_router(teams.router, prefix="/api")
    application.include_router(players.router, prefix="/api")
    application.include_router(standings.router, prefix="/api")

    return application


app = create_app()
