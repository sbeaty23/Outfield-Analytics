from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.providers.base import BaseballDataProvider
from app.services.player_service import PlayerService
from app.services.standings_service import StandingsService
from app.services.team_service import TeamService


def get_baseball_provider(request: Request) -> BaseballDataProvider:
    return request.app.state.baseball_provider


def get_team_service(
    provider: Annotated[BaseballDataProvider, Depends(get_baseball_provider)],
    session: Annotated[Session, Depends(get_db)],
) -> TeamService:
    return TeamService(provider, session)


def get_player_service(
    provider: Annotated[BaseballDataProvider, Depends(get_baseball_provider)],
) -> PlayerService:
    return PlayerService(provider)


def get_standings_service(
    provider: Annotated[BaseballDataProvider, Depends(get_baseball_provider)],
) -> StandingsService:
    return StandingsService(provider)
