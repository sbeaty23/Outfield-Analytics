from fastapi import APIRouter, HTTPException, status

from app.database.session import is_database_connected
from app.schemas.error import ErrorResponse
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The API is running but PostgreSQL is unavailable.",
            "model": ErrorResponse,
        },
    },
)
def get_health() -> HealthResponse:
    if is_database_connected():
        return HealthResponse(status="ok", database="connected")

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database unavailable",
    )
