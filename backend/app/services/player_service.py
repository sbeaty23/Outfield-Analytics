from app.providers.base import BaseballDataProvider
from app.schemas.player import Player
from app.schemas.stats import PlayerStats


class PlayerService:
    def __init__(self, provider: BaseballDataProvider):
        self._provider = provider

    async def get_player(self, player_id: int) -> Player:
        return await self._provider.get_player(player_id)

    async def get_stats(self, player_id: int, group: str) -> PlayerStats:
        return await self._provider.get_player_stats(player_id, group)
