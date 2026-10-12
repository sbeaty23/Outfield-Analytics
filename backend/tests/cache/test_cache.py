import asyncio
from datetime import UTC, date, datetime, timedelta

import pytest
from redis.exceptions import ConnectionError

from app.cache.base import CachePolicy, CacheStatus
from app.cache.keys import (
    player_stats_key,
    roster_key,
    schedule_key,
    team_stats_key,
)
from app.cache.service import CacheService
from app.schemas.roster import Roster


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expirations: dict[str, int] = {}
        self.fail = False
        self.closed = False

    async def get(self, key: str):
        if self.fail:
            raise ConnectionError()
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ex: int):
        if self.fail:
            raise ConnectionError()
        self.values[key] = value
        self.expirations[key] = ex

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            count += key in self.values
            self.values.pop(key, None)
        return count

    async def scan_iter(self, *, match: str, count: int):
        prefix = match.removesuffix("*")
        for key in list(self.values):
            if key.startswith(prefix):
                yield key

    async def ping(self) -> bool:
        if self.fail:
            raise ConnectionError()
        return True

    async def aclose(self) -> None:
        self.closed = True


def test_cache_keys_are_season_aware_and_deterministic() -> None:
    assert roster_key(2026, 110) == "outfield:mlb:v1:2026:team:110:roster:active"
    assert team_stats_key(2026, 110, "hitting").endswith("stats:hitting")
    assert player_stats_key(2026, 123, "pitching").endswith("stats:pitching")
    assert schedule_key(2026, 110, date(2026, 6, 1), date(2026, 6, 3)).endswith(
        "schedule:2026-06-01:2026-06-03"
    )


def test_cache_policy_requires_a_larger_hard_ttl() -> None:
    with pytest.raises(ValueError):
        CachePolicy(timedelta(minutes=30), timedelta(minutes=30))


def test_cache_classifies_fresh_stale_and_expired_values() -> None:
    async def run() -> None:
        client = FakeRedis()
        cache = CacheService(client, enabled=True, operation_timeout=1)
        policy = CachePolicy(timedelta(minutes=30), timedelta(hours=6))
        fetched_at = datetime(2026, 1, 1, tzinfo=UTC)
        value = Roster(team_id=110, season=2026, players=[])
        assert await cache.set("key", value, policy, now=fetched_at)
        assert client.expirations["key"] == 21600

        fresh = await cache.get("key", Roster, now=fetched_at + timedelta(minutes=29))
        stale = await cache.get("key", Roster, now=fetched_at + timedelta(minutes=31))
        expired = await cache.get("key", Roster, now=fetched_at + timedelta(hours=6))
        assert fresh.status == CacheStatus.HIT
        assert stale.status == CacheStatus.STALE
        assert expired.status == CacheStatus.MISS
        assert "key" not in client.values

    asyncio.run(run())


def test_invalid_cache_data_is_deleted_and_treated_as_a_miss() -> None:
    async def run() -> None:
        client = FakeRedis()
        client.values["key"] = "not-json"
        cache = CacheService(client, enabled=True, operation_timeout=1)
        result = await cache.get("key", Roster)
        assert result.status == CacheStatus.MISS
        assert "key" not in client.values

    asyncio.run(run())


def test_disabled_and_unavailable_cache_bypass_without_raising() -> None:
    async def run() -> None:
        disabled = CacheService(None, enabled=False, operation_timeout=1)
        assert (await disabled.get("key", Roster)).status == CacheStatus.BYPASS
        assert await disabled.status() == "disabled"

        client = FakeRedis()
        client.fail = True
        unavailable = CacheService(client, enabled=True, operation_timeout=1)
        assert (await unavailable.get("key", Roster)).status == CacheStatus.BYPASS
        assert not await unavailable.set(
            "key",
            Roster(team_id=110, season=2026, players=[]),
            CachePolicy(timedelta(seconds=1), timedelta(seconds=2)),
        )
        assert await unavailable.status() == "unavailable"

    asyncio.run(run())


def test_namespace_clear_does_not_delete_unrelated_data() -> None:
    async def run() -> None:
        client = FakeRedis()
        client.values = {
            "outfield:mlb:v1:2026:teams": "value",
            "outfield:mlb:v1:2026:standings": "value",
            "unrelated:key": "value",
        }
        cache = CacheService(client, enabled=True, operation_timeout=1)
        assert await cache.delete_namespace() == 2
        assert client.values == {"unrelated:key": "value"}

    asyncio.run(run())
