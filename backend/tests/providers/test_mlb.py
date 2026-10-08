import asyncio

import httpx2 as httpx
import pytest

from app.core.config import Settings
from app.providers.exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderTimeoutError,
)
from app.providers.mlb import MLBProvider


def team_payload(**overrides):
    return {
        "id": 110,
        "name": "Baltimore Orioles",
        "abbreviation": "BAL",
        "locationName": "Baltimore",
        "league": {"id": 103, "name": "American League", "link": "/ignored"},
        "division": {"name": "American League East"},
        "venue": {"name": "Oriole Park at Camden Yards"},
        "sport": {"id": 1},
        "active": True,
        "link": "/ignored",
        **overrides,
    }


def run_provider(handler, method="get_teams", *args):
    async def run():
        settings = Settings(
            _env_file=None,
            mlb_api_base_url="https://baseball.test/custom/v1/",
            mlb_current_season=2026,
            mlb_request_timeout_seconds=7,
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await getattr(MLBProvider(client, settings), method)(*args)

    return asyncio.run(run())


def test_teams_are_normalized_and_filtered_to_active_mlb():
    def handler(request):
        assert str(request.url).startswith("https://baseball.test/custom/v1/teams?")
        assert dict(request.url.params) == {
            "sportId": "1",
            "activeStatus": "Y",
            "season": "2026",
        }
        assert request.extensions["timeout"]["read"] == 7
        return httpx.Response(
            200,
            json={
                "teams": [
                    team_payload(),
                    team_payload(id=999, sport={"id": 11}),
                    team_payload(id=998, active=False),
                ]
            },
        )

    result = run_provider(handler)
    assert result.season == 2026
    assert [team.id for team in result.teams] == [110]
    assert result.teams[0].location == "Baltimore"
    assert result.teams[0].league == "American League"
    assert "link" not in result.model_dump_json()
    assert "locationName" not in result.model_dump_json()


def test_roster_is_active_normalized_and_current_season():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.params["season"] == "2026"
        if request.url.path.endswith("/roster"):
            assert request.url.params["rosterType"] == "active"
            return httpx.Response(
                200,
                json={
                    "roster": [
                        {
                            "person": {
                                "id": 123,
                                "fullName": "Example Player",
                                "link": "/ignore",
                            },
                            "position": {"name": "Catcher"},
                            "status": {"description": "Active"},
                        }
                    ]
                },
            )
        return httpx.Response(200, json={"teams": [team_payload()]})

    result = run_provider(handler, "get_roster", 110)
    assert len(requests) == 2
    assert result.model_dump() == {
        "team_id": 110,
        "season": 2026,
        "roster_type": "active",
        "players": [
            {
                "player_id": 123,
                "full_name": "Example Player",
                "jersey_number": None,
                "position_name": "Catcher",
                "position_abbreviation": None,
                "position_type": None,
                "status": "Active",
            }
        ],
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"teams": []},
        {"teams": [team_payload(sport={"id": 11})]},
        {"teams": [team_payload(active=False)]},
        {"teams": [team_payload(id=111)]},
    ],
)
def test_team_not_in_scope_is_not_found(payload):
    with pytest.raises(ProviderNotFoundError):
        run_provider(lambda _: httpx.Response(200, json=payload), "get_team", 110)


@pytest.mark.parametrize(
    "status, exception",
    [
        (404, ProviderNotFoundError),
        (429, ProviderError),
        (500, ProviderError),
        (302, ProviderError),
    ],
)
def test_http_errors_are_translated(status, exception):
    with pytest.raises(exception):
        run_provider(lambda _: httpx.Response(status, text="upstream private detail"))


@pytest.mark.parametrize(
    "error, expected",
    [
        (httpx.ReadTimeout("private"), ProviderTimeoutError),
        (httpx.ConnectError("private"), ProviderError),
    ],
)
def test_network_errors_are_translated(error, expected):
    def handler(request):
        raise error

    with pytest.raises(expected):
        run_provider(handler)


@pytest.mark.parametrize("payload", [{}, {"teams": None}, {"teams": [{}]}])
def test_invalid_payload_is_provider_error(payload):
    with pytest.raises(ProviderError):
        run_provider(lambda _: httpx.Response(200, json=payload))


def test_invalid_json_is_provider_error():
    with pytest.raises(ProviderError):
        run_provider(lambda _: httpx.Response(200, text="not json"))


@pytest.mark.parametrize("content_length", ["2000001", "invalid"])
def test_oversized_or_invalid_content_length_is_provider_error(content_length):
    with pytest.raises(ProviderError):
        run_provider(
            lambda _: httpx.Response(
                200,
                headers={"Content-Length": content_length},
                content=b"{}",
            )
        )


def test_empty_roster_is_valid():
    def handler(request):
        payload = (
            {"roster": []}
            if request.url.path.endswith("/roster")
            else {"teams": [team_payload()]}
        )
        return httpx.Response(200, json=payload)

    assert run_provider(handler, "get_roster", 110).players == []


def test_minor_league_roster_is_rejected_before_roster_request():
    def handler(request):
        assert not request.url.path.endswith("/roster")
        return httpx.Response(200, json={"teams": [team_payload(sport={"id": 11})]})

    with pytest.raises(ProviderNotFoundError):
        run_provider(handler, "get_roster", 110)


@pytest.mark.parametrize("payload", [{}, {"roster": [{}]}])
def test_malformed_roster_is_not_treated_as_empty(payload):
    def handler(request):
        return httpx.Response(
            200,
            json=payload
            if request.url.path.endswith("/roster")
            else {"teams": [team_payload()]},
        )

    with pytest.raises(ProviderError):
        run_provider(handler, "get_roster", 110)
