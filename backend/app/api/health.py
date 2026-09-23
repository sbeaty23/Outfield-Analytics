from fastapi import APIRouter, Response, status

from app.database.session import is_database_connected
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The API is running but PostgreSQL is unavailable.",
            "model": HealthResponse,
        },
    },
)
def get_health(response: Response) -> HealthResponse:
    if is_database_connected():
        return HealthResponse(status="ok", database="connected")

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="degraded", database="unavailable")
