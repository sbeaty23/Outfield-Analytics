import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


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
