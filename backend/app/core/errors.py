import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.providers.exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderTimeoutError,
)
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


async def handle_provider_error(request: Request, error: ProviderError) -> JSONResponse:
    if isinstance(error, ProviderNotFoundError):
        code, detail = 404, "Baseball resource not found"
    elif isinstance(error, ProviderTimeoutError):
        code, detail = 504, "Baseball data provider timed out"
    else:
        code, detail = 502, "Baseball data provider unavailable"
    logger.warning("Baseball provider failure type=%s", type(error).__name__)
    return JSONResponse(status_code=code, content={"detail": detail})


async def handle_unexpected_error(
    request: Request,
    error: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled request error method=%s type=%s",
        request.method,
        type(error).__name__,
        # Exception messages and tracebacks can contain request or connection secrets.
        exc_info=None,
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
