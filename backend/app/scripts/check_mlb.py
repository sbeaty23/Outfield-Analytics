"""Explicit, bounded live acceptance check; never part of the offline test suite."""

import asyncio
from datetime import date

import httpx2 as httpx

from app.core.config import settings
from app.providers.mlb import MLBProvider
from app.services.schedule_policy import schedule_range


async def check() -> None:
    async with httpx.AsyncClient(follow_redirects=False) as client:
        provider = MLBProvider(client, settings)
        teams = await provider.get_teams()
        assert len(teams.teams) == 30, "Expected 30 active MLB teams"
        team_id = teams.teams[0].id
        await provider.get_team(team_id)
        roster = await provider.get_roster(team_id)
        assert roster.players, "Expected an active roster"
        for group in ("hitting", "pitching", "fielding"):
            result = await provider.get_team_stats(team_id, group)
            assert result.stats is not None, f"No current team {group} statistics"
            print(f"PASS team {group}")
        standings = await provider.get_standings()
        assert len(standings.divisions) == 6, "Expected six divisions"
        assert sum(len(d.teams) for d in standings.divisions) == 30
        start = date.today()
        if start.year != settings.mlb_current_season:
            start = date(settings.mlb_current_season, 7, 1)
        start, end = schedule_range(settings.mlb_current_season, start, None)
        await provider.get_schedule(team_id, start, end)
        for group, pitcher in (("hitting", False), ("pitching", True)):
            candidates = [
                p for p in roster.players if (p.position_type == "Pitcher") == pitcher
            ]
            for player in candidates[:3]:
                await provider.get_player(player.player_id)
                result = await provider.get_player_stats(player.player_id, group)
                if result.stats is not None:
                    break
            else:
                raise AssertionError(
                    "No applicable statistics in bounded player sample"
                )
            print(f"PASS player profile and {group}")
        print("PASS teams=30, roster, standings=6 divisions, current schedule")


if __name__ == "__main__":
    try:
        asyncio.run(check())
    except Exception as error:
        # Never print a transport exception containing configured connection values.
        print(f"FAIL live MLB acceptance: {type(error).__name__}")
        raise SystemExit(1) from None
