import asyncio
import os
from datetime import timedelta

import pytest
import redis.asyncio as redis

from app.cache.base import CachePolicy, CacheStatus
from app.cache.service import CacheService
from app.schemas.roster import Roster


@pytest.mark.redis_integration
@pytest.mark.skipif(
    not os.getenv("REDIS_INTEGRATION_URL"),
    reason="REDIS_INTEGRATION_URL is not configured",
)
def test_real_redis_round_trip_and_namespace_cleanup() -> None:
    async def run() -> None:
        client = redis.from_url(
            os.environ["REDIS_INTEGRATION_URL"], decode_responses=True
        )
        cache = CacheService(client, enabled=True, operation_timeout=2)
        key = "outfield:mlb:v1:2026:integration:roster"
        try:
            value = Roster(team_id=110, season=2026, players=[])
            policy = CachePolicy(timedelta(seconds=10), timedelta(seconds=30))
            assert await cache.set(key, value, policy)
            result = await cache.get(key, Roster)
            assert result.status == CacheStatus.HIT
            assert result.data == value
            assert await cache.delete_namespace() >= 1
        finally:
            await cache.close()

    asyncio.run(run())
