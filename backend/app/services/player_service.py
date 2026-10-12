from app.cache.keys import player_key, player_stats_key
from app.cache.loader import CachedResourceLoader
from app.cache.policies import REFERENCE_POLICY, STATS_POLICY
from app.core.config import settings
from app.providers.base import BaseballDataProvider
from app.schemas.player import Player
from app.schemas.stats import PlayerStats


class PlayerService:
    def __init__(
        self,
        provider: BaseballDataProvider,
        cache: CachedResourceLoader | None = None,
    ):
        self._provider = provider
        self._cache = cache

    async def get_player(self, player_id: int) -> Player:
        if self._cache is None:
            return await self._provider.get_player(player_id)
        return await self._cache.load(
            key=player_key(settings.mlb_current_season, player_id),
            model_type=Player,
            policy=REFERENCE_POLICY,
            fetch=lambda: self._provider.get_player(player_id),
            resource="player",
            player_id=player_id,
        )

    async def get_stats(self, player_id: int, group: str) -> PlayerStats:
        if self._cache is None:
            return await self._provider.get_player_stats(player_id, group)
        return await self._cache.load(
            key=player_stats_key(settings.mlb_current_season, player_id, group),
            model_type=PlayerStats,
            policy=STATS_POLICY,
            fetch=lambda: self._provider.get_player_stats(player_id, group),
            resource=f"player_stats_{group}",
            player_id=player_id,
        )
