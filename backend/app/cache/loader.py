import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

from app.cache.base import CachedResult, CachePolicy, CacheStatus
from app.cache.service import CacheService
from app.providers.exceptions import ProviderUnavailableError

logger = logging.getLogger(__name__)
ModelT = TypeVar("ModelT", bound=BaseModel)


class CachedResourceLoader:
    def __init__(self, cache: CacheService) -> None:
        self._cache = cache
        self._inflight: dict[str, asyncio.Task] = {}
        self._guard = asyncio.Lock()

    @property
    def inflight_count(self) -> int:
        return len(self._inflight)

    async def load(
        self,
        *,
        key: str,
        model_type: type[ModelT],
        policy: CachePolicy,
        fetch: Callable[[], Awaitable[ModelT]],
        resource: str,
        team_id: int | None = None,
        player_id: int | None = None,
    ) -> ModelT:
        cached = await self._cache.get(key, model_type)
        self._log_lookup(resource, cached.status, team_id, player_id)
        if cached.status == CacheStatus.HIT and cached.data is not None:
            return cached.data

        async with self._guard:
            task = self._inflight.get(key)
            if task is None:
                task = asyncio.create_task(
                    self._refresh(
                        key=key,
                        model_type=model_type,
                        policy=policy,
                        fetch=fetch,
                        resource=resource,
                        initial=cached,
                        team_id=team_id,
                        player_id=player_id,
                    )
                )
                self._inflight[key] = task

        return await asyncio.shield(task)

    async def _refresh(
        self,
        *,
        key: str,
        model_type: type[ModelT],
        policy: CachePolicy,
        fetch: Callable[[], Awaitable[ModelT]],
        resource: str,
        initial: CachedResult[ModelT],
        team_id: int | None,
        player_id: int | None,
    ) -> ModelT:
        try:
            checked = await self._cache.get(key, model_type)
            if checked.status == CacheStatus.HIT and checked.data is not None:
                self._log_lookup(resource, checked.status, team_id, player_id)
                return checked.data
            stale = checked if checked.status == CacheStatus.STALE else initial
            try:
                value = await fetch()
            except ProviderUnavailableError as error:
                if stale.status == CacheStatus.STALE and stale.data is not None:
                    logger.warning(
                        "event=cache_fallback resource=%s cache_status=stale "
                        "team_id=%s player_id=%s error=%s",
                        resource,
                        team_id or "none",
                        player_id or "none",
                        type(error).__name__,
                    )
                    return stale.data
                raise
            await self._cache.set(key, value, policy)
            return value
        finally:
            async with self._guard:
                if self._inflight.get(key) is asyncio.current_task():
                    self._inflight.pop(key, None)

    @staticmethod
    def _log_lookup(
        resource: str,
        status: CacheStatus,
        team_id: int | None,
        player_id: int | None,
    ) -> None:
        logger.info(
            "event=cache_lookup resource=%s cache_status=%s team_id=%s player_id=%s",
            resource,
            status.value,
            team_id or "none",
            player_id or "none",
        )
