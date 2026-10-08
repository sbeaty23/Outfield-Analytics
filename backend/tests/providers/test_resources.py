from datetime import date

import httpx2 as httpx
import pytest

from app.providers.exceptions import ProviderError, ProviderNotFoundError
from tests.providers.test_mlb import run_provider, team_payload


def resource_handler(payload):
    def handler(request):
        assert request.url.params["season"] == "2026"
        path = request.url.path
        if path.endswith("/teams/110"):
            return httpx.Response(200, json={"teams": [team_payload()]})
        if path.endswith("/people/123"):
            return httpx.Response(
                200,
                json={
                    "people": [{"id": 123, "fullName": "Test Player", "active": True}]
                },
            )
        return httpx.Response(200, json=payload)

    return handler


@pytest.mark.parametrize(
    "group,stat,field,expected",
    [
        ("hitting", {"hits": 0, "avg": ".284"}, "average", 0.284),
        (
            "pitching",
            {"inningsPitched": "6.1", "era": "2.34"},
            "innings_pitched",
            "6.1",
        ),
        ("fielding", {"fielding": ".987"}, "fielding_percentage", 0.987),
    ],
)
def test_team_statistics(group, stat, field, expected):
    result = run_provider(
        resource_handler({"stats": [{"splits": [{"stat": stat}]}]}),
        "get_team_stats",
        110,
        group,
    )
    assert getattr(result.stats, field) == expected
    assert result.stats.games is None
    if group == "hitting":
        assert result.stats.hits == 0


@pytest.mark.parametrize("group", ["hitting", "pitching"])
def test_player_statistics(group):
    result = run_provider(
        resource_handler({"stats": [{"splits": [{"stat": {"hits": "4"}}]}]}),
        "get_player_stats",
        123,
        group,
    )
    assert result.stats.hits == 4


@pytest.mark.parametrize("payload", [{"stats": []}, {"stats": [{"splits": []}]}])
def test_empty_statistics(payload):
    assert (
        run_provider(resource_handler(payload), "get_team_stats", 110, "hitting").stats
        is None
    )


@pytest.mark.parametrize(
    "stat", [None, [], "bad", {"hits": "NaN"}, {"hits": "1.5"}, {"avg": "Infinity"}]
)
def test_malformed_statistics(stat):
    with pytest.raises(ProviderError):
        run_provider(
            resource_handler({"stats": [{"splits": [{"stat": stat}]}]}),
            "get_team_stats",
            110,
            "hitting",
        )


def test_player_profile():
    result = run_provider(resource_handler({}), "get_player", 123)
    assert result.full_name == "Test Player"
    assert result.primary_position is None


def test_missing_player():
    with pytest.raises(ProviderNotFoundError):
        run_provider(
            lambda _: httpx.Response(200, json={"people": []}), "get_player", 123
        )


def test_schedule_normalization_and_parameters():
    def handler(request):
        if request.url.path.endswith("/teams/110"):
            return httpx.Response(200, json={"teams": [team_payload()]})
        assert request.url.params["teamId"] == "110"
        assert request.url.params["startDate"] == "2026-06-01"
        assert request.url.params["endDate"] == "2026-06-03"
        return httpx.Response(
            200,
            json={
                "dates": [
                    {
                        "games": [
                            {
                                "gamePk": 1,
                                "gameDate": "2026-06-01T12:00:00Z",
                                "gameType": "R",
                                "teams": {
                                    "away": {"team": {"id": 110, "name": "Away"}},
                                    "home": {"team": {"id": 111, "name": "Home"}},
                                },
                                "status": {"detailedState": "Scheduled"},
                            }
                        ]
                    }
                ]
            },
        )

    result = run_provider(
        handler, "get_schedule", 110, date(2026, 6, 1), date(2026, 6, 3)
    )
    assert result.games[0].probable_home_pitcher is None
    assert result.games[0].away_score is None


def test_standings_normalization():
    payload = {
        "records": [
            {
                "division": {"id": 201, "name": "AL East"},
                "teamRecords": [
                    {
                        "team": {"id": 110, "name": "Test"},
                        "wins": 4,
                        "losses": 2,
                        "winningPercentage": ".667",
                        "gamesBack": "-",
                        "divisionRank": "1",
                        "leagueRank": "2",
                    }
                ],
            }
        ]
    }
    result = run_provider(resource_handler(payload), "get_standings")
    row = result.divisions[0].teams[0]
    assert row.winning_percentage == 0.667
    assert row.division_rank == 1
    assert row.last_ten_wins is None


@pytest.mark.parametrize(
    "method,args,payload",
    [
        ("get_standings", (), {"records": [None]}),
        ("get_player", (123,), {"people": [None]}),
        ("get_roster", (110,), {"roster": [{"person": None}]}),
        ("get_schedule", (110, date(2026, 6, 1), date(2026, 6, 2)), {"dates": [None]}),
    ],
)
def test_malformed_resources(method, args, payload):
    def handler(request):
        if request.url.path.endswith("/teams/110"):
            return httpx.Response(200, json={"teams": [team_payload()]})
        return httpx.Response(200, json=payload)

    with pytest.raises(ProviderError):
        run_provider(handler, method, *args)


def test_provider_rejects_historical_schedule_without_request():
    def handler(_):
        pytest.fail("Invalid dates reached upstream")

    with pytest.raises(ProviderError):
        run_provider(handler, "get_schedule", 110, date(2011, 6, 1), date(2011, 6, 2))
