from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.cache.service import CacheService
from app.database.session import is_database_connected
from app.schemas.diagnostics import DiagnosticsResponse

router = APIRouter(tags=["diagnostics"])


@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def get_diagnostics(request: Request) -> DiagnosticsResponse:
    cache: CacheService = request.app.state.cache_service
    database_connected = await run_in_threadpool(is_database_connected)
    return DiagnosticsResponse(
        database="connected" if database_connected else "unavailable",
        redis=await cache.status(),
        mlb_provider="configured",
    )
