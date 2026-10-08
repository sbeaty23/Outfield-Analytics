import asyncio
from datetime import date
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.team import Team
from app.schemas.team import Team as TeamData
from app.scripts.sync_teams import persist_teams
from app.services.schedule_policy import schedule_range
from app.services.team_service import TeamService


@pytest.mark.parametrize(
    "start,end",
    [
        (date(2026, 1, 1), date(2026, 2, 1)),
        (date(2026, 2, 2), date(2026, 2, 1)),
        (date(2011, 1, 1), date(2011, 1, 2)),
        (date(2026, 12, 31), date(2027, 1, 1)),
    ],
)
def test_invalid_schedule(start, end):
    with pytest.raises(ValueError):
        schedule_range(2026, start, end)


def test_schedule_defaults_and_inclusive_limit():
    assert schedule_range(2026, date(2026, 1, 1), date(2026, 1, 31))[1] == date(
        2026, 1, 31
    )
    assert schedule_range(2026, None, None, today=date(2026, 12, 29)) == (
        date(2026, 12, 29),
        date(2026, 12, 31),
    )
    with pytest.raises(ValueError):
        schedule_range(2026, None, None, today=date(2027, 1, 1))


def test_sync_and_database_read(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'teams.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine)
    team = TeamData(
        id=110,
        name="Test Club",
        abbreviation="TST",
        location="Test",
        league="Test League",
        active=True,
    )
    assert persist_teams([team], factory) == (1, 1, 0)
    with factory() as session:
        internal_id = session.scalar(select(Team.id))
    team.name = "Renamed Club"
    assert persist_teams([team], factory) == (1, 0, 1)
    with factory() as session:
        rows = list(session.scalars(select(Team)))
        assert len(rows) == 1 and rows[0].id == internal_id
        provider = AsyncMock()
        result = asyncio.run(TeamService(provider, session).get_team(110))
        assert result.name == "Renamed Club"
        provider.get_team.assert_not_called()
    with pytest.raises(ValueError):
        persist_teams([team, team], factory)
    broken = team.model_copy(update={"name": None})
    with pytest.raises(SQLAlchemyError):
        persist_teams([broken], factory)
    with factory() as session:
        assert session.scalar(select(Team.name)) == "Renamed Club"
    engine.dispose()


def test_database_failure_rolls_back_before_provider_fallback():
    session = Mock()
    session.scalar.side_effect = SQLAlchemyError("private")
    provider = AsyncMock()
    asyncio.run(TeamService(provider, session).get_team(110))
    session.rollback.assert_called_once()
    provider.get_team.assert_awaited_once_with(110)
