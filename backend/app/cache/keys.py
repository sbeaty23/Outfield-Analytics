from datetime import date


def _prefix(season: int) -> str:
    return f"outfield:mlb:v1:{season}"


def namespace_prefix() -> str:
    return "outfield:mlb:v1:"


def teams_key(season: int) -> str:
    return f"{_prefix(season)}:teams"


def team_key(season: int, team_id: int) -> str:
    return f"{_prefix(season)}:team:{team_id}"


def roster_key(season: int, team_id: int) -> str:
    return f"{team_key(season, team_id)}:roster:active"


def team_stats_key(season: int, team_id: int, group: str) -> str:
    return f"{team_key(season, team_id)}:stats:{group}"


def schedule_key(season: int, team_id: int, start_date: date, end_date: date) -> str:
    return (
        f"{team_key(season, team_id)}:schedule:"
        f"{start_date.isoformat()}:{end_date.isoformat()}"
    )


def standings_key(season: int) -> str:
    return f"{_prefix(season)}:standings"


def player_key(season: int, player_id: int) -> str:
    return f"{_prefix(season)}:player:{player_id}"


def player_stats_key(season: int, player_id: int, group: str) -> str:
    return f"{player_key(season, player_id)}:stats:{group}"
