import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


async def handle_unexpected_error(
    request: Request,
    error: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled request error method=%s type=%s",
        request.method,
        type(error).__name__,
        exc_info=error if settings.environment == "development" else None,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(detail="Internal server error").model_dump(),
    )


async def handle_validation_error(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    # FastAPI's default validation details can echo sensitive input values.
    return JSONResponse(
        status_code=422, content={"detail": "Request validation failed"}
    )
