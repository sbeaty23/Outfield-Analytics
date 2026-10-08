from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_baseball_provider
from app.database.session import get_db
from app.main import create_app
from app.providers.base import BaseballDataProvider
from app.providers.exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderTimeoutError,
)
from app.schemas.player import Player
from app.schemas.schedule import TeamSchedule
from app.schemas.standings import Standings
from app.schemas.stats import PlayerStats, TeamStats


@pytest.fixture
def resources():
    provider = AsyncMock(spec=BaseballDataProvider)
    provider.get_team_stats.side_effect = lambda team, group: TeamStats(
        team_id=team, season=2026, group=group, stats=None
    )
    provider.get_player_stats.side_effect = lambda player, group: PlayerStats(
        player_id=player, season=2026, group=group, stats=None
    )
    provider.get_player.return_value = Player(
        id=123, full_name="Test Player", active=True
    )
    provider.get_standings.return_value = Standings(season=2026, divisions=[])
    provider.get_schedule.return_value = TeamSchedule(
        team_id=110, season=2026, games=[]
    )
    app = create_app()
    app.dependency_overrides[get_baseball_provider] = lambda: provider
    app.dependency_overrides[get_db] = lambda: None
    with TestClient(app) as client:
        yield client, provider


PATHS = [
    ("/api/teams/110/stats/hitting", "get_team_stats"),
    ("/api/teams/110/stats/pitching", "get_team_stats"),
    ("/api/teams/110/stats/fielding", "get_team_stats"),
    (
        "/api/teams/110/schedule?start_date=2026-06-01&end_date=2026-06-03",
        "get_schedule",
    ),
    ("/api/players/123", "get_player"),
    ("/api/players/123/stats/hitting", "get_player_stats"),
    ("/api/players/123/stats/pitching", "get_player_stats"),
    ("/api/standings", "get_standings"),
]


@pytest.mark.parametrize("path,method", PATHS)
def test_resource_routes(resources, path, method):
    client, provider = resources
    response = client.get(path)
    assert response.status_code == 200
    getattr(provider, method).assert_awaited_once()
    if method == "get_schedule":
        provider.get_schedule.assert_awaited_once_with(
            110, date(2026, 6, 1), date(2026, 6, 3)
        )


@pytest.mark.parametrize("path,method", PATHS)
@pytest.mark.parametrize(
    "error,status",
    [(ProviderError, 502), (ProviderNotFoundError, 404), (ProviderTimeoutError, 504)],
)
def test_resource_errors(resources, path, method, error, status):
    client, provider = resources
    getattr(provider, method).side_effect = error("private upstream detail")
    response = client.get(path)
    assert response.status_code == status
    assert "private" not in response.text


@pytest.mark.parametrize("path,method", PATHS)
def test_season_override_rejected(resources, path, method):
    client, provider = resources
    separator = "&" if "?" in path else "?"
    assert client.get(path + separator + "season=2011").status_code == 422
    getattr(provider, method).assert_not_awaited()


@pytest.mark.parametrize(
    "query",
    [
        "start_date=2011-01-01&end_date=2011-01-02",
        "start_date=2026-01-01&end_date=2026-02-01",
        "start_date=bad",
        "start_date=2026-12-31&end_date=2027-01-01",
    ],
)
def test_invalid_schedule_never_calls_provider(resources, query):
    client, provider = resources
    assert client.get("/api/teams/110/schedule?" + query).status_code == 422
    provider.get_schedule.assert_not_awaited()


def test_openapi_sections(resources):
    client, _ = resources
    schema = client.get("/openapi.json").json()
    tags = {
        tag
        for methods in schema["paths"].values()
        for operation in methods.values()
        for tag in operation.get("tags", [])
    }
    assert {"health", "teams", "players", "standings"} <= tags
