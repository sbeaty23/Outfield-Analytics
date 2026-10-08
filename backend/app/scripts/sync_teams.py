import asyncio

import httpx2 as httpx
from sqlalchemy import select

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.team import Team
from app.providers.mlb import MLBProvider
from app.schemas.team import Team as TeamData


async def sync_teams() -> tuple[int, int, int]:
    async with httpx.AsyncClient(
        follow_redirects=False,
        trust_env=False,
        limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
    ) as client:
        source = (await MLBProvider(client, settings).get_teams()).teams
    return persist_teams(source)


def persist_teams(
    source: list[TeamData], session_factory=SessionLocal
) -> tuple[int, int, int]:
    if len({item.id for item in source}) != len(source):
        raise ValueError("Duplicate MLB identifiers in team response")
    inserted = updated = 0
    with session_factory.begin() as session:
        existing = {team.mlb_id: team for team in session.scalars(select(Team))}
        for item in source:
            values = {
                "name": item.name,
                "location_name": item.location,
                "team_name": item.team_name,
                "abbreviation": item.abbreviation,
                "league_id": item.league_id,
                "league_name": item.league,
                "division_id": item.division_id,
                "division_name": item.division,
                "active": item.active,
            }
            if item.id in existing:
                for key, value in values.items():
                    setattr(existing[item.id], key, value)
                updated += 1
            else:
                session.add(Team(mlb_id=item.id, **values))
                inserted += 1
    return len(source), inserted, updated


if __name__ == "__main__":
    try:
        found, inserted, updated = asyncio.run(sync_teams())
    except Exception as error:
        print(f"Team synchronization failed: {type(error).__name__}")
        raise SystemExit(1) from None
    print(f"Found: {found}; Inserted: {inserted}; Updated: {updated}")
