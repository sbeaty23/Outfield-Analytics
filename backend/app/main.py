import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import APP_TITLE, APP_VERSION, settings
from app.core.errors import handle_unexpected_error, handle_validation_error
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.database.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    configure_logging()
    logger.info("Outfield Analytics application started")
    try:
        yield
    finally:
        engine.dispose()
        logger.info("Outfield Analytics application stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        lifespan=lifespan,
    )

    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )
    application.add_exception_handler(Exception, handle_unexpected_error)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.include_router(health.router, prefix="/api")

    return application


app = create_app()
