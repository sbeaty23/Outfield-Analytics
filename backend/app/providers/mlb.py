"""MLB transport and normalization; upstream dictionaries never leave here."""

import asyncio
import json
import logging
import math
from datetime import date
from functools import wraps
from time import perf_counter
from typing import Any

import httpx2 as httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import Settings
from app.providers.base import BaseballDataProvider
from app.providers.exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderTimeoutError,
)
from app.schemas.player import Player
from app.schemas.roster import Roster, RosterPlayer
from app.schemas.schedule import ScheduledGame, TeamSchedule
from app.schemas.standings import DivisionStandings, StandingEntry, Standings
from app.schemas.stats import (
    FieldingStats,
    HittingStats,
    PitchingStats,
    PlayerStats,
    TeamStats,
)
from app.schemas.team import Team, TeamList
from app.services.schedule_policy import schedule_range

logger = logging.getLogger(__name__)


def normalized_resource(method):
    @wraps(method)
    async def wrapped(self, *args, **kwargs):
        started = perf_counter()
        outcome = "success"
        try:
            return await method(self, *args, **kwargs)
        except ProviderTimeoutError:
            outcome = "timeout"
            raise
        except ProviderNotFoundError:
            outcome = "not_found"
            raise
        except ProviderError:
            outcome = "provider_error"
            raise
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            AttributeError,
            OverflowError,
        ) as error:
            outcome = "invalid_response"
            raise ProviderError() from error
        finally:
            logger.info(
                "provider=mlb resource=%s identifier=%s status=%s duration_ms=%d",
                method.__name__,
                args[0] if args and isinstance(args[0], int) else "none",
                outcome,
                int((perf_counter() - started) * 1000),
            )

    return wrapped


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


class _Named(_Model):
    id: int | None = None
    name: str | None = None


class _Team(_Model):
    id: int
    name: str
    abbreviation: str
    location_name: str = Field(alias="locationName")
    team_name: str | None = Field(default=None, alias="teamName")
    league: _Named
    division: _Named | None = None
    venue: _Named | None = None
    sport: _Named
    active: bool

    def normalized(self) -> Team:
        return Team(
            id=self.id,
            name=self.name,
            abbreviation=self.abbreviation,
            location=self.location_name,
            team_name=self.team_name,
            league_id=self.league.id,
            league=self.league.name,
            division_id=self.division.id if self.division else None,
            division=self.division.name if self.division else None,
            venue=self.venue.name if self.venue else None,
            active=self.active,
        )


class _Teams(_Model):
    teams: list[_Team]


def _list(value: Any) -> list:
    if not isinstance(value, list):
        raise ValueError("Expected a list")
    return value


def _number(value: Any) -> float | None:
    if value in (None, "", "-.--", ".---", "--", "---"):
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite statistic")
    return result


def _integer(stat: dict[str, Any], key: str) -> int | None:
    value = stat.get(key)
    if value is None or value == "":
        return None
    number = float(value)
    if not math.isfinite(number) or not number.is_integer() or isinstance(value, bool):
        raise ValueError("Invalid counting statistic")
    return int(number)


class MLBProvider(BaseballDataProvider):
    def __init__(self, client: httpx.AsyncClient, settings: Settings):
        self._client = client
        self._base_url = str(settings.mlb_api_base_url).rstrip("/")
        self._sport_id = settings.mlb_sport_id
        self._season = settings.mlb_current_season
        self._timeout = settings.mlb_request_timeout_seconds
        self._request_slots = asyncio.Semaphore(settings.mlb_max_concurrent_requests)
        self._max_response_bytes = settings.mlb_max_response_bytes

    async def _get(self, path: str, **params: str | int) -> Any:
        started = perf_counter()
        resource = path.split("/")[0]
        params["season"] = self._season
        try:
            async with self._request_slots:
                async with self._client.stream(
                    "GET",
                    f"{self._base_url}/{path}",
                    params=params,
                    timeout=self._timeout,
                ) as response:
                    if response.status_code == 404:
                        raise ProviderNotFoundError()
                    response.raise_for_status()
                    declared_size = response.headers.get("content-length")
                    if declared_size and int(declared_size) > self._max_response_bytes:
                        raise ProviderError()
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self._max_response_bytes:
                            raise ProviderError()
            result = json.loads(body)
            logger.info(
                "provider=mlb resource=%s status=success duration_ms=%d",
                resource,
                int((perf_counter() - started) * 1000),
            )
            return result
        except httpx.TimeoutException as error:
            logger.warning("provider=mlb resource=%s status=timeout", resource)
            raise ProviderTimeoutError() from error
        except ProviderNotFoundError:
            raise
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("provider=mlb resource=%s status=error", resource)
            raise ProviderError() from error

    async def _teams(self, path: str, **params: str | int) -> list[Team]:
        try:
            values = _Teams.model_validate(await self._get(path, **params)).teams
            return [
                x.normalized()
                for x in values
                if x.active and x.sport.id == self._sport_id
            ]
        except ValidationError as error:
            raise ProviderError() from error

    @normalized_resource
    async def get_teams(self) -> TeamList:
        return TeamList(
            season=self._season,
            teams=await self._teams("teams", sportId=self._sport_id, activeStatus="Y"),
        )

    @normalized_resource
    async def get_team(self, team_id: int) -> Team:
        teams = await self._teams(f"teams/{team_id}", sportId=self._sport_id)
        if teams and teams[0].id == team_id:
            return teams[0]
        raise ProviderNotFoundError()

    @normalized_resource
    async def get_roster(self, team_id: int) -> Roster:
        await self.get_team(team_id)
        payload = await self._get(
            f"teams/{team_id}/roster", rosterType="active", hydrate="person"
        )
        try:
            players = []
            for entry in _list(payload["roster"]):
                person, position = entry["person"], entry.get("position") or {}
                players.append(
                    RosterPlayer(
                        player_id=person["id"],
                        full_name=person["fullName"],
                        jersey_number=entry.get("jerseyNumber"),
                        position_name=position.get("name")
                        or (person.get("primaryPosition") or {}).get("name"),
                        position_abbreviation=position.get("abbreviation"),
                        position_type=position.get("type"),
                        status=(entry.get("status") or {}).get("description"),
                    )
                )
            return Roster(team_id=team_id, season=self._season, players=players)
        except (KeyError, TypeError, ValidationError) as error:
            raise ProviderError() from error

    def _normalize_stats(self, stat: dict[str, Any], group: str):
        if not isinstance(stat, dict):
            raise ValueError("Invalid statistics object")
        if group == "hitting":
            return HittingStats(
                games=_integer(stat, "gamesPlayed"),
                plate_appearances=_integer(stat, "plateAppearances"),
                at_bats=_integer(stat, "atBats"),
                runs=_integer(stat, "runs"),
                hits=_integer(stat, "hits"),
                doubles=_integer(stat, "doubles"),
                triples=_integer(stat, "triples"),
                home_runs=_integer(stat, "homeRuns"),
                rbi=_integer(stat, "rbi"),
                walks=_integer(stat, "baseOnBalls"),
                strikeouts=_integer(stat, "strikeOuts"),
                average=_number(stat.get("avg")),
                obp=_number(stat.get("obp")),
                slg=_number(stat.get("slg")),
                ops=_number(stat.get("ops")),
            )
        if group == "pitching":
            return PitchingStats(
                games=_integer(stat, "gamesPlayed"),
                wins=_integer(stat, "wins"),
                losses=_integer(stat, "losses"),
                innings_pitched=stat.get("inningsPitched"),
                hits=_integer(stat, "hits"),
                runs=_integer(stat, "runs"),
                earned_runs=_integer(stat, "earnedRuns"),
                home_runs=_integer(stat, "homeRuns"),
                walks=_integer(stat, "baseOnBalls"),
                strikeouts=_integer(stat, "strikeOuts"),
                era=_number(stat.get("era")),
                whip=_number(stat.get("whip")),
            )
        return FieldingStats(
            games=_integer(stat, "gamesPlayed"),
            games_started=_integer(stat, "gamesStarted"),
            innings=stat.get("innings"),
            putouts=_integer(stat, "putOuts"),
            assists=_integer(stat, "assists"),
            errors=_integer(stat, "errors"),
            fielding_percentage=_number(stat.get("fielding")),
        )

    async def _stats(self, path: str, group: str):
        payload = await self._get(path, stats="season", group=group, gameType="R")
        try:
            blocks = payload["stats"]
            if not isinstance(blocks, list):
                raise ValueError("Invalid statistics list")
            if not blocks:
                return None
            splits = blocks[0]["splits"]
            if not isinstance(splits, list):
                raise ValueError("Invalid statistics splits")
            if not splits:
                return None
            return self._normalize_stats(splits[0]["stat"], group)
        except (KeyError, IndexError, TypeError, ValueError, ValidationError) as error:
            raise ProviderError() from error

    @normalized_resource
    async def get_team_stats(self, team_id: int, group: str) -> TeamStats:
        await self.get_team(team_id)
        return TeamStats(
            team_id=team_id,
            season=self._season,
            group=group,
            stats=await self._stats(f"teams/{team_id}/stats", group),
        )

    @normalized_resource
    async def get_player_stats(self, player_id: int, group: str) -> PlayerStats:
        await self.get_player(player_id)
        return PlayerStats(
            player_id=player_id,
            season=self._season,
            group=group,
            stats=await self._stats(f"people/{player_id}/stats", group),
        )

    @normalized_resource
    async def get_player(self, player_id: int) -> Player:
        payload = await self._get(f"people/{player_id}", hydrate="currentTeam")
        try:
            people = _list(payload["people"])
            if people == []:
                raise ProviderNotFoundError()
            p = people[0]
            if p["id"] != player_id:
                raise ProviderNotFoundError()
            return Player(
                id=p["id"],
                full_name=p["fullName"],
                first_name=p.get("firstName"),
                last_name=p.get("lastName"),
                jersey_number=p.get("primaryNumber"),
                primary_position=(p.get("primaryPosition") or {}).get("name"),
                bat_side=(p.get("batSide") or {}).get("description"),
                throw_side=(p.get("pitchHand") or {}).get("description"),
                height=p.get("height"),
                weight=p.get("weight"),
                active=p["active"],
                current_team_id=(p.get("currentTeam") or {}).get("id"),
            )
        except (KeyError, IndexError, TypeError, ValidationError) as error:
            raise ProviderError() from error

    @normalized_resource
    async def get_schedule(
        self, team_id: int, start_date: date, end_date: date
    ) -> TeamSchedule:
        schedule_range(self._season, start_date, end_date)
        await self.get_team(team_id)
        payload = await self._get(
            "schedule",
            sportId=self._sport_id,
            teamId=team_id,
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            hydrate="probablePitcher",
        )
        try:
            games = []
            for day in _list(payload["dates"]):
                for game in _list(day["games"]):
                    away, home = game["teams"]["away"], game["teams"]["home"]
                    games.append(
                        ScheduledGame(
                            game_id=game["gamePk"],
                            game_date=game["gameDate"],
                            game_type=game["gameType"],
                            away_team_id=away["team"]["id"],
                            away_team_name=away["team"]["name"],
                            home_team_id=home["team"]["id"],
                            home_team_name=home["team"]["name"],
                            away_score=away.get("score"),
                            home_score=home.get("score"),
                            status=game["status"]["detailedState"],
                            venue_name=(game.get("venue") or {}).get("name"),
                            probable_home_pitcher=(
                                home.get("probablePitcher") or {}
                            ).get("fullName"),
                            probable_away_pitcher=(
                                away.get("probablePitcher") or {}
                            ).get("fullName"),
                        )
                    )
            return TeamSchedule(team_id=team_id, season=self._season, games=games)
        except (KeyError, TypeError, ValidationError) as error:
            raise ProviderError() from error

    @normalized_resource
    async def get_standings(self) -> Standings:
        payload = await self._get(
            "standings",
            leagueId="103,104",
            standingsTypes="regularSeason",
            hydrate="division",
        )
        try:
            divisions = []
            for record in _list(payload["records"]):
                entries = []
                for row in _list(record["teamRecords"]):
                    last_ten = next(
                        (
                            x
                            for x in row.get("records", {}).get("splitRecords", [])
                            if x.get("type") == "lastTen"
                        ),
                        {},
                    )
                    entries.append(
                        StandingEntry(
                            team_id=row["team"]["id"],
                            team_name=row["team"]["name"],
                            wins=row["wins"],
                            losses=row["losses"],
                            winning_percentage=_number(row["winningPercentage"]),
                            games_back=row["gamesBack"],
                            division_rank=int(row["divisionRank"])
                            if row.get("divisionRank")
                            else None,
                            league_rank=int(row["leagueRank"])
                            if row.get("leagueRank")
                            else None,
                            last_ten_wins=_integer(last_ten, "wins"),
                            last_ten_losses=_integer(last_ten, "losses"),
                            streak=(row.get("streak") or {}).get("streakCode"),
                        )
                    )
                d = record["division"]
                divisions.append(
                    DivisionStandings(
                        division_id=d["id"], division_name=d["name"], teams=entries
                    )
                )
            return Standings(season=self._season, divisions=divisions)
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            raise ProviderError() from error
