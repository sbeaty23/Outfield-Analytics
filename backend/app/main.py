import logging
from typing import Literal

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["not_configured"]


class ErrorResponse(BaseModel):
    detail: str


def create_app() -> FastAPI:
    application = FastAPI(
        title="Outfield Analytics API",
        version="0.1.0",
    )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        error: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled request error for %s %s",
            request.method,
            request.url.path,
            exc_info=error,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(detail="Internal server error").model_dump(),
        )

    @application.get(
        "/api/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
    )
    async def get_health() -> HealthResponse:
        return HealthResponse(status="ok", database="not_configured")

    return application


app = create_app()
