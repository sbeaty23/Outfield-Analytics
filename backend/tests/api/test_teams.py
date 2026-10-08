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
from app.schemas.roster import Roster
from app.schemas.team import Team, TeamList


@pytest.fixture
def client_and_provider():
    provider = AsyncMock(spec=BaseballDataProvider)
    team = Team(
        id=110,
        name="Baltimore Orioles",
        abbreviation="BAL",
        location="Baltimore",
        league="American League",
        active=True,
    )
    provider.get_teams.return_value = TeamList(season=2026, teams=[team])
    provider.get_team.return_value = team
    provider.get_roster.return_value = Roster(team_id=110, season=2026, players=[])
    application = create_app()
    application.dependency_overrides[get_baseball_provider] = lambda: provider
    application.dependency_overrides[get_db] = lambda: None
    with TestClient(application) as client:
        yield client, provider


@pytest.mark.parametrize(
    "path, method, arguments",
    [
        ("/api/teams", "get_teams", ()),
        ("/api/teams/110", "get_team", (110,)),
        ("/api/teams/110/roster", "get_roster", (110,)),
    ],
)
def test_routes_use_service_and_swappable_provider(
    client_and_provider, path, method, arguments
):
    client, provider = client_and_provider
    response = client.get(path)
    assert response.status_code == 200
    getattr(provider, method).assert_awaited_once_with(*arguments)
    assert response.json() == getattr(provider, method).return_value.model_dump()


@pytest.mark.parametrize(
    "path", ["/api/teams", "/api/teams/110", "/api/teams/110/roster"]
)
@pytest.mark.parametrize(
    "query",
    ["season=2011", "season=2026", "date=2011-06-01", "sportId=11", "rosterType=40Man"],
)
def test_query_overrides_rejected_before_provider_call(
    client_and_provider, path, query
):
    client, provider = client_and_provider
    assert client.get(f"{path}?{query}").status_code == 422
    provider.get_teams.assert_not_awaited()
    provider.get_team.assert_not_awaited()
    provider.get_roster.assert_not_awaited()


@pytest.mark.parametrize("team_id", ["0", "-1", "abc"])
def test_invalid_team_id(client_and_provider, team_id):
    client, provider = client_and_provider
    assert client.get(f"/api/teams/{team_id}/roster").status_code == 422
    provider.get_roster.assert_not_awaited()


@pytest.mark.parametrize(
    "error, status",
    [
        (ProviderError, 502),
        (ProviderTimeoutError, 504),
        (ProviderNotFoundError, 404),
    ],
)
def test_provider_failures_have_safe_http_responses(client_and_provider, error, status):
    client, provider = client_and_provider
    provider.get_teams.side_effect = error("private upstream detail")
    response = client.get("/api/teams")
    assert response.status_code == status
    assert "private" not in response.text
