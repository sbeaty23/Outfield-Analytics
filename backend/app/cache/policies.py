from datetime import timedelta

from app.cache.base import CachePolicy

REFERENCE_POLICY = CachePolicy(
    fresh_ttl=timedelta(hours=24), hard_ttl=timedelta(hours=72)
)
ROSTER_POLICY = CachePolicy(fresh_ttl=timedelta(hours=6), hard_ttl=timedelta(hours=24))
STATS_POLICY = CachePolicy(fresh_ttl=timedelta(minutes=30), hard_ttl=timedelta(hours=6))
FIELDING_STATS_POLICY = CachePolicy(
    fresh_ttl=timedelta(minutes=60), hard_ttl=timedelta(hours=6)
)
STANDINGS_POLICY = CachePolicy(
    fresh_ttl=timedelta(minutes=30), hard_ttl=timedelta(hours=6)
)
SCHEDULE_POLICY = CachePolicy(fresh_ttl=timedelta(hours=2), hard_ttl=timedelta(hours=6))


def team_stats_policy(group: str) -> CachePolicy:
    return FIELDING_STATS_POLICY if group == "fielding" else STATS_POLICY
