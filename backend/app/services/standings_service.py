from app.providers.base import BaseballDataProvider
from app.schemas.standings import Standings


class StandingsService:
    def __init__(self, provider: BaseballDataProvider):
        self._provider = provider

    async def get_standings(self) -> Standings:
        return await self._provider.get_standings()
