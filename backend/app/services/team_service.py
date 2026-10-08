import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

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
    def __init__(self, provider: BaseballDataProvider, session: Session | None = None):
        self._provider = provider
        self._session = session

    async def get_teams(self) -> TeamList:
        return await self._provider.get_teams()

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
        return await self._provider.get_team(team_id)

    async def get_roster(self, team_id: int) -> Roster:
        return await self._provider.get_roster(team_id)

    async def get_stats(self, team_id: int, group: str) -> TeamStats:
        return await self._provider.get_team_stats(team_id, group)

    async def get_schedule(
        self, team_id: int, start_date: date | None, end_date: date | None
    ) -> TeamSchedule:
        try:
            start, end = schedule_range(
                settings.mlb_current_season, start_date, end_date
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return await self._provider.get_schedule(team_id, start, end)
