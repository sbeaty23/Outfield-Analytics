import asyncio
import json
import logging
from datetime import UTC, datetime
from math import ceil
from typing import Literal, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel, ValidationError
from redis.exceptions import RedisError

from app.cache.base import CachedResult, CachePolicy, CacheStatus
from app.cache.keys import namespace_prefix
from app.core.config import Settings

logger = logging.getLogger(__name__)
ModelT = TypeVar("ModelT", bound=BaseModel)
RedisStatus = Literal["connected", "unavailable", "disabled"]


class CacheService:
    def __init__(
        self,
        client: redis.Redis | None,
        *,
        enabled: bool,
        operation_timeout: float,
    ) -> None:
        self._client = client
        self._enabled = enabled
        self._operation_timeout = operation_timeout

    @classmethod
    def from_settings(cls, settings: Settings) -> "CacheService":
        client = None
        if settings.cache_enabled and settings.redis_url is not None:
            client = redis.from_url(
                str(settings.redis_url),
                decode_responses=True,
                socket_connect_timeout=settings.redis_connect_timeout_seconds,
                socket_timeout=settings.redis_operation_timeout_seconds,
                max_connections=settings.redis_max_connections,
            )
        return cls(
            client,
            enabled=settings.cache_enabled,
            operation_timeout=settings.redis_operation_timeout_seconds,
        )

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    async def get(
        self,
        key: str,
        model_type: type[ModelT],
        *,
        now: datetime | None = None,
    ) -> CachedResult[ModelT]:
        if not self.enabled:
            return CachedResult(data=None, status=CacheStatus.BYPASS)

        try:
            async with asyncio.timeout(self._operation_timeout):
                raw = await self._client.get(key)  # type: ignore[union-attr]
        except (RedisError, TimeoutError):
            logger.warning("event=cache_read status=bypass error=redis_unavailable")
            return CachedResult(data=None, status=CacheStatus.BYPASS)

        if raw is None:
            return CachedResult(data=None, status=CacheStatus.MISS)

        try:
            envelope = json.loads(raw)
            fetched_at = datetime.fromisoformat(envelope["fetched_at"])
            fresh_until = datetime.fromisoformat(envelope["fresh_until"])
            stale_until = datetime.fromisoformat(envelope["stale_until"])
            if any(
                value.tzinfo is None for value in (fetched_at, fresh_until, stale_until)
            ):
                raise ValueError("Cache timestamps must be timezone-aware")
            data = model_type.model_validate(envelope["data"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError):
            logger.warning("event=cache_read status=miss error=invalid_envelope")
            await self.delete(key)
            return CachedResult(data=None, status=CacheStatus.MISS)

        current = now or datetime.now(UTC)
        if current >= stale_until:
            await self.delete(key)
            return CachedResult(data=None, status=CacheStatus.MISS)
        if current < fresh_until:
            return CachedResult(
                data=data, status=CacheStatus.HIT, fetched_at=fetched_at
            )
        return CachedResult(data=data, status=CacheStatus.STALE, fetched_at=fetched_at)

    async def set(
        self,
        key: str,
        value: BaseModel,
        policy: CachePolicy,
        *,
        now: datetime | None = None,
    ) -> bool:
        if not self.enabled:
            return False
        fetched_at = now or datetime.now(UTC)
        envelope = {
            "data": value.model_dump(mode="json"),
            "fetched_at": fetched_at.isoformat(),
            "fresh_until": (fetched_at + policy.fresh_ttl).isoformat(),
            "stale_until": (fetched_at + policy.hard_ttl).isoformat(),
        }
        try:
            async with asyncio.timeout(self._operation_timeout):
                await self._client.set(  # type: ignore[union-attr]
                    key,
                    json.dumps(envelope, separators=(",", ":")),
                    ex=ceil(policy.hard_ttl.total_seconds()),
                )
            return True
        except (RedisError, TimeoutError):
            logger.warning("event=cache_write status=bypass error=redis_unavailable")
            return False

    async def delete(self, key: str) -> bool:
        if not self.enabled:
            return False
        try:
            async with asyncio.timeout(self._operation_timeout):
                await self._client.delete(key)  # type: ignore[union-attr]
            return True
        except (RedisError, TimeoutError):
            logger.warning("event=cache_delete status=bypass error=redis_unavailable")
            return False

    async def delete_namespace(self) -> int:
        if not self.enabled:
            return 0
        deleted = 0
        batch: list[str] = []
        try:
            async with asyncio.timeout(self._operation_timeout):
                async for key in self._client.scan_iter(  # type: ignore[union-attr]
                    match=f"{namespace_prefix()}*", count=100
                ):
                    batch.append(key)
                    if len(batch) == 100:
                        deleted += await self._client.delete(*batch)  # type: ignore[union-attr]
                        batch.clear()
                if batch:
                    deleted += await self._client.delete(*batch)  # type: ignore[union-attr]
            return deleted
        except (RedisError, TimeoutError):
            logger.warning("event=cache_clear status=failed error=redis_unavailable")
            return 0

    async def status(self) -> RedisStatus:
        if not self.enabled:
            return "disabled"
        try:
            async with asyncio.timeout(self._operation_timeout):
                connected = await self._client.ping()  # type: ignore[union-attr]
            return "connected" if connected else "unavailable"
        except (RedisError, TimeoutError):
            return "unavailable"

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
