import asyncio

from app.cache.service import CacheService
from app.core.config import settings


async def clear_cache() -> int:
    cache = CacheService.from_settings(settings)
    try:
        if await cache.status() != "connected":
            raise RuntimeError("Cache is not connected")
        deleted = await cache.delete_namespace()
        if await cache.status() != "connected":
            raise RuntimeError("Cache became unavailable while clearing entries")
        return deleted
    finally:
        await cache.close()


def main() -> None:
    deleted = asyncio.run(clear_cache())
    print(f"Deleted {deleted} Outfield Analytics cache entries")


if __name__ == "__main__":
    main()
