from app.cache.keys import standings_key
from app.cache.loader import CachedResourceLoader
from app.cache.policies import STANDINGS_POLICY
from app.core.config import settings
from app.providers.base import BaseballDataProvider
from app.schemas.standings import Standings


class StandingsService:
    def __init__(
        self,
        provider: BaseballDataProvider,
        cache: CachedResourceLoader | None = None,
    ):
        self._provider = provider
        self._cache = cache

    async def get_standings(self) -> Standings:
        if self._cache is None:
            return await self._provider.get_standings()
        return await self._cache.load(
            key=standings_key(settings.mlb_current_season),
            model_type=Standings,
            policy=STANDINGS_POLICY,
            fetch=self._provider.get_standings,
            resource="standings",
        )
