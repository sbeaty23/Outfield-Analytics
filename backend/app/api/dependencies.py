from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.cache.loader import CachedResourceLoader
from app.database.session import get_db
from app.providers.base import BaseballDataProvider
from app.services.player_service import PlayerService
from app.services.standings_service import StandingsService
from app.services.team_service import TeamService


def get_baseball_provider(request: Request) -> BaseballDataProvider:
    return request.app.state.baseball_provider


def get_cached_resource_loader(request: Request) -> CachedResourceLoader:
    return request.app.state.cached_resource_loader


def get_team_service(
    provider: Annotated[BaseballDataProvider, Depends(get_baseball_provider)],
    cache: Annotated[CachedResourceLoader, Depends(get_cached_resource_loader)],
    session: Annotated[Session, Depends(get_db)],
) -> TeamService:
    return TeamService(provider, session, cache)


def get_player_service(
    provider: Annotated[BaseballDataProvider, Depends(get_baseball_provider)],
    cache: Annotated[CachedResourceLoader, Depends(get_cached_resource_loader)],
) -> PlayerService:
    return PlayerService(provider, cache)


def get_standings_service(
    provider: Annotated[BaseballDataProvider, Depends(get_baseball_provider)],
    cache: Annotated[CachedResourceLoader, Depends(get_cached_resource_loader)],
) -> StandingsService:
    return StandingsService(provider, cache)
