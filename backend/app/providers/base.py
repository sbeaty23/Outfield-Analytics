from abc import ABC, abstractmethod
from datetime import date

from app.schemas.player import Player
from app.schemas.roster import Roster
from app.schemas.schedule import TeamSchedule
from app.schemas.standings import Standings
from app.schemas.stats import PlayerStats, TeamStats
from app.schemas.team import Team, TeamList


class BaseballDataProvider(ABC):
    @abstractmethod
    async def get_teams(self) -> TeamList: ...
    @abstractmethod
    async def get_team(self, team_id: int) -> Team: ...
    @abstractmethod
    async def get_roster(self, team_id: int) -> Roster: ...
    @abstractmethod
    async def get_team_stats(self, team_id: int, group: str) -> TeamStats: ...
    @abstractmethod
    async def get_schedule(
        self, team_id: int, start_date: date, end_date: date
    ) -> TeamSchedule: ...
    @abstractmethod
    async def get_standings(self) -> Standings: ...
    @abstractmethod
    async def get_player(self, player_id: int) -> Player: ...
    @abstractmethod
    async def get_player_stats(self, player_id: int, group: str) -> PlayerStats: ...
