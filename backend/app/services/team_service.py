import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.cache.keys import (
    roster_key,
    schedule_key,
    team_key,
    team_stats_key,
    teams_key,
)
from app.cache.loader import CachedResourceLoader
from app.cache.policies import (
    REFERENCE_POLICY,
    ROSTER_POLICY,
    SCHEDULE_POLICY,
    team_stats_policy,
)
from app.core.config import settings
from app.models.team import Team as TeamRecord
from app.providers.base import BaseballDataProvider
from app.schemas.roster import Roster
from app.schemas.schedule import TeamSchedule
from app.schemas.stats import TeamStats
from app.schemas.team import Team, TeamList
from app.services.schedule_policy import schedule_range

logger = logging.getLogger(__name__)


class TeamService:
    def __init__(
        self,
        provider: BaseballDataProvider,
        session: Session | None = None,
        cache: CachedResourceLoader | None = None,
    ):
        self._provider = provider
        self._session = session
        self._cache = cache

    async def get_teams(self) -> TeamList:
        if self._cache is None:
            return await self._provider.get_teams()
        return await self._cache.load(
            key=teams_key(settings.mlb_current_season),
            model_type=TeamList,
            policy=REFERENCE_POLICY,
            fetch=self._provider.get_teams,
            resource="teams",
        )

    async def get_team(self, team_id: int) -> Team:
        if self._session is not None:
            try:
                record = await run_in_threadpool(
                    self._session.scalar,
                    select(TeamRecord).where(TeamRecord.mlb_id == team_id),
                )
                if record is not None:
                    return Team(
                        id=record.mlb_id,
                        name=record.name,
                        abbreviation=record.abbreviation,
                        location=record.location_name,
                        team_name=record.team_name,
                        league_id=record.league_id,
                        league=record.league_name,
                        division_id=record.division_id,
                        division=record.division_name,
                        active=record.active,
                    )
            except SQLAlchemyError:
                await run_in_threadpool(self._session.rollback)
                logger.warning("Team database read failed; using provider fallback")
        if self._cache is None:
            return await self._provider.get_team(team_id)
        return await self._cache.load(
            key=team_key(settings.mlb_current_season, team_id),
            model_type=Team,
            policy=REFERENCE_POLICY,
            fetch=lambda: self._provider.get_team(team_id),
            resource="team",
            team_id=team_id,
        )

    async def get_roster(self, team_id: int) -> Roster:
        if self._cache is None:
            return await self._provider.get_roster(team_id)
        return await self._cache.load(
            key=roster_key(settings.mlb_current_season, team_id),
            model_type=Roster,
            policy=ROSTER_POLICY,
            fetch=lambda: self._provider.get_roster(team_id),
            resource="roster",
            team_id=team_id,
        )

    async def get_stats(self, team_id: int, group: str) -> TeamStats:
        if self._cache is None:
            return await self._provider.get_team_stats(team_id, group)
        return await self._cache.load(
            key=team_stats_key(settings.mlb_current_season, team_id, group),
            model_type=TeamStats,
            policy=team_stats_policy(group),
            fetch=lambda: self._provider.get_team_stats(team_id, group),
            resource=f"team_stats_{group}",
            team_id=team_id,
        )

    async def get_schedule(
        self, team_id: int, start_date: date | None, end_date: date | None
    ) -> TeamSchedule:
        try:
            start, end = schedule_range(
                settings.mlb_current_season, start_date, end_date
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if self._cache is None:
            return await self._provider.get_schedule(team_id, start, end)
        return await self._cache.load(
            key=schedule_key(settings.mlb_current_season, team_id, start, end),
            model_type=TeamSchedule,
            policy=SCHEDULE_POLICY,
            fetch=lambda: self._provider.get_schedule(team_id, start, end),
            resource="schedule",
            team_id=team_id,
        )
