import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.cache.base import CachedResult, CacheStatus
from app.cache.loader import CachedResourceLoader
from app.cache.policies import ROSTER_POLICY
from app.providers.exceptions import ProviderError, ProviderUnavailableError
from app.schemas.roster import Roster


class FakeCache:
    def __init__(self, result: CachedResult) -> None:
        self.result = result
        self.set_calls = 0

    async def get(self, key, model_type):
        return self.result

    async def set(self, key, value, policy):
        self.set_calls += 1
        self.result = CachedResult(
            data=value, status=CacheStatus.HIT, fetched_at=datetime.now(UTC)
        )
        return True


def test_fresh_cache_prevents_provider_call() -> None:
    async def run() -> None:
        roster = Roster(team_id=110, season=2026, players=[])
        cache = FakeCache(CachedResult(roster, CacheStatus.HIT))
        provider = AsyncMock()
        result = await CachedResourceLoader(cache).load(
            key="key",
            model_type=Roster,
            policy=ROSTER_POLICY,
            fetch=provider,
            resource="roster",
            team_id=110,
        )
        assert result is roster
        provider.assert_not_awaited()

    asyncio.run(run())


def test_stale_value_is_only_used_for_unavailable_provider() -> None:
    async def run() -> None:
        roster = Roster(team_id=110, season=2026, players=[])
        cache = FakeCache(CachedResult(roster, CacheStatus.STALE))
        unavailable = AsyncMock(side_effect=ProviderUnavailableError())
        result = await CachedResourceLoader(cache).load(
            key="key",
            model_type=Roster,
            policy=ROSTER_POLICY,
            fetch=unavailable,
            resource="roster",
        )
        assert result is roster

        malformed = AsyncMock(side_effect=ProviderError())
        with pytest.raises(ProviderError):
            await CachedResourceLoader(cache).load(
                key="other",
                model_type=Roster,
                policy=ROSTER_POLICY,
                fetch=malformed,
                resource="roster",
            )

    asyncio.run(run())


def test_concurrent_misses_share_one_provider_request_and_cleanup() -> None:
    async def run() -> None:
        cache = FakeCache(CachedResult(None, CacheStatus.MISS))
        roster = Roster(team_id=110, season=2026, players=[])
        started = asyncio.Event()
        release = asyncio.Event()
        calls = 0

        async def fetch():
            nonlocal calls
            calls += 1
            started.set()
            await release.wait()
            return roster

        loader = CachedResourceLoader(cache)
        tasks = [
            asyncio.create_task(
                loader.load(
                    key="key",
                    model_type=Roster,
                    policy=ROSTER_POLICY,
                    fetch=fetch,
                    resource="roster",
                )
            )
            for _ in range(10)
        ]
        await started.wait()
        release.set()
        results = await asyncio.gather(*tasks)
        assert results == [roster] * 10
        assert calls == 1
        assert cache.set_calls == 1
        assert loader.inflight_count == 0

    asyncio.run(run())


def test_cache_bypass_still_returns_provider_data() -> None:
    async def run() -> None:
        cache = FakeCache(CachedResult(None, CacheStatus.BYPASS))
        roster = Roster(team_id=110, season=2026, players=[])
        provider = AsyncMock(return_value=roster)
        result = await CachedResourceLoader(cache).load(
            key="key",
            model_type=Roster,
            policy=ROSTER_POLICY,
            fetch=provider,
            resource="roster",
        )
        assert result is roster
        provider.assert_awaited_once()

    asyncio.run(run())
