import asyncio
from unittest.mock import AsyncMock

from app.providers.base import BaseballDataProvider
from app.schemas.roster import Roster
from app.services.team_service import TeamService


def test_service_uses_provider_contract_without_mlb_dependencies():
    provider = AsyncMock(spec=BaseballDataProvider)
    expected = Roster(team_id=110, season=2026, players=[])
    provider.get_roster.return_value = expected

    result = asyncio.run(TeamService(provider).get_roster(110))

    assert result is expected
    provider.get_roster.assert_awaited_once_with(110)
