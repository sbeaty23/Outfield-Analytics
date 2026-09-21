from fastapi import APIRouter, status

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok", database="not_configured")
