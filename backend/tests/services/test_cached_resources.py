import asyncio
from datetime import date
from unittest.mock import AsyncMock

from app.cache.base import CachedResult, CacheStatus
from app.cache.loader import CachedResourceLoader
from app.providers.base import BaseballDataProvider
from app.schemas.player import Player
from app.schemas.roster import Roster
from app.schemas.schedule import TeamSchedule
from app.schemas.standings import Standings
from app.schemas.stats import PlayerStats, TeamStats
from app.schemas.team import Team, TeamList
from app.services.player_service import PlayerService
from app.services.standings_service import StandingsService
from app.services.team_service import TeamService


class MemoryCache:
    def __init__(self) -> None:
        self.values = {}

    async def get(self, key, model_type):
        value = self.values.get(key)
        if value is None:
            return CachedResult(None, CacheStatus.MISS)
        return CachedResult(value, CacheStatus.HIT)

    async def set(self, key, value, policy):
        self.values[key] = value
        return True


def test_all_provider_backed_service_resources_are_cached() -> None:
    async def run() -> None:
        provider = AsyncMock(spec=BaseballDataProvider)
        team = Team(
            id=110,
            name="Test Club",
            abbreviation="TST",
            location="Test",
            league="Test League",
            active=True,
        )
        provider.get_teams.return_value = TeamList(season=2026, teams=[team])
        provider.get_team.return_value = team
        provider.get_roster.return_value = Roster(team_id=110, season=2026, players=[])
        provider.get_team_stats.return_value = TeamStats(
            team_id=110, season=2026, group="hitting", stats=None
        )
        provider.get_schedule.return_value = TeamSchedule(
            team_id=110, season=2026, games=[]
        )
        provider.get_player.return_value = Player(
            id=123, full_name="Test Player", active=True
        )
        provider.get_player_stats.return_value = PlayerStats(
            player_id=123, season=2026, group="hitting", stats=None
        )
        provider.get_standings.return_value = Standings(season=2026, divisions=[])

        loader = CachedResourceLoader(MemoryCache())
        teams = TeamService(provider, cache=loader)
        players = PlayerService(provider, cache=loader)
        standings = StandingsService(provider, cache=loader)

        operations = [
            (teams.get_teams, ()),
            (teams.get_team, (110,)),
            (teams.get_roster, (110,)),
            (teams.get_stats, (110, "hitting")),
            (teams.get_schedule, (110, date(2026, 6, 1), date(2026, 6, 3))),
            (players.get_player, (123,)),
            (players.get_stats, (123, "hitting")),
            (standings.get_standings, ()),
        ]
        for operation, arguments in operations:
            first = await operation(*arguments)
            second = await operation(*arguments)
            assert second == first

        provider.get_teams.assert_awaited_once()
        provider.get_team.assert_awaited_once()
        provider.get_roster.assert_awaited_once()
        provider.get_team_stats.assert_awaited_once()
        provider.get_schedule.assert_awaited_once()
        provider.get_player.assert_awaited_once()
        provider.get_player_stats.assert_awaited_once()
        provider.get_standings.assert_awaited_once()

    asyncio.run(run())
