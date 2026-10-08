from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_standings_service
from app.api.teams import current_season_only
from app.schemas.standings import Standings
from app.services.standings_service import StandingsService

router = APIRouter(
    prefix="/standings", tags=["standings"], dependencies=[Depends(current_season_only)]
)
Service = Annotated[StandingsService, Depends(get_standings_service)]


@router.get("", response_model=Standings, summary="Get current MLB standings")
async def get_standings(service: Service) -> Standings:
    return await service.get_standings()
