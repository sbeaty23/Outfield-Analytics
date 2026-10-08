from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.dependencies import get_team_service
from app.schemas.roster import Roster
from app.schemas.schedule import TeamSchedule
from app.schemas.stats import TeamStats
from app.schemas.team import Team, TeamList
from app.services.team_service import TeamService


def current_season_only(
    season: str | None = Query(default=None),
    date_override: str | None = Query(default=None, alias="date"),
    sport_id: str | None = Query(default=None, alias="sportId"),
    roster_type: str | None = Query(default=None, alias="rosterType"),
) -> None:
    if any(
        value is not None for value in (season, date_override, sport_id, roster_type)
    ):
        raise HTTPException(
            status_code=422, detail="Current-season query overrides are not allowed"
        )


router = APIRouter(
    prefix="/teams", tags=["teams"], dependencies=[Depends(current_season_only)]
)
TeamServiceDependency = Annotated[TeamService, Depends(get_team_service)]
TeamId = Annotated[int, Path(gt=0)]


@router.get("", response_model=TeamList)
async def get_teams(service: TeamServiceDependency) -> TeamList:
    return await service.get_teams()


@router.get("/{team_id}", response_model=Team)
async def get_team(team_id: TeamId, service: TeamServiceDependency) -> Team:
    return await service.get_team(team_id)


@router.get("/{team_id}/roster", response_model=Roster)
async def get_roster(team_id: TeamId, service: TeamServiceDependency) -> Roster:
    return await service.get_roster(team_id)


@router.get("/{team_id}/stats/{group}", response_model=TeamStats)
async def get_stats(
    team_id: TeamId,
    group: Literal["hitting", "pitching", "fielding"],
    service: TeamServiceDependency,
) -> TeamStats:
    return await service.get_stats(team_id, group)


@router.get("/{team_id}/schedule", response_model=TeamSchedule)
async def get_schedule(
    team_id: TeamId,
    service: TeamServiceDependency,
    start_date: date | None = None,
    end_date: date | None = None,
) -> TeamSchedule:
    return await service.get_schedule(team_id, start_date, end_date)
