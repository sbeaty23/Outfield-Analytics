from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel


class CacheStatus(StrEnum):
    HIT = "hit"
    MISS = "miss"
    STALE = "stale"
    BYPASS = "bypass"


@dataclass(frozen=True)
class CachePolicy:
    fresh_ttl: timedelta
    hard_ttl: timedelta

    def __post_init__(self) -> None:
        if self.fresh_ttl.total_seconds() <= 0:
            raise ValueError("fresh_ttl must be positive")
        if self.hard_ttl <= self.fresh_ttl:
            raise ValueError("hard_ttl must be greater than fresh_ttl")


ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(frozen=True)
class CachedResult(Generic[ModelT]):
    data: ModelT | None
    status: CacheStatus
    fetched_at: datetime | None = None
