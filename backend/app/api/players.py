from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path

from app.api.dependencies import get_player_service
from app.api.teams import current_season_only
from app.schemas.player import Player
from app.schemas.stats import PlayerStats
from app.services.player_service import PlayerService

router = APIRouter(
    prefix="/players", tags=["players"], dependencies=[Depends(current_season_only)]
)
Service = Annotated[PlayerService, Depends(get_player_service)]
PlayerId = Annotated[int, Path(gt=0)]


@router.get(
    "/{player_id}", response_model=Player, summary="Get a current player profile"
)
async def get_player(player_id: PlayerId, service: Service) -> Player:
    return await service.get_player(player_id)


@router.get(
    "/{player_id}/stats/{group}",
    response_model=PlayerStats,
    summary="Get current player statistics",
)
async def get_player_stats(
    player_id: PlayerId, group: Literal["hitting", "pitching"], service: Service
) -> PlayerStats:
    return await service.get_stats(player_id, group)
