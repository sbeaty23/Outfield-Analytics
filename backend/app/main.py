from fastapi import FastAPI

from app.api import health
from app.core.config import APP_TITLE, APP_VERSION
from app.core.errors import handle_unexpected_error


def create_app() -> FastAPI:
    application = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
    )

    application.add_exception_handler(Exception, handle_unexpected_error)
    application.include_router(health.router, prefix="/api")

    return application


app = create_app()
