from pydantic import BaseModel, Field


class HittingStats(BaseModel):
    games: int | None = None
    plate_appearances: int | None = None
    at_bats: int | None = None
    runs: int | None = None
    hits: int | None = None
    doubles: int | None = None
    triples: int | None = None
    home_runs: int | None = None
    rbi: int | None = None
    walks: int | None = None
    strikeouts: int | None = None
    average: float | None = None
    obp: float | None = None
    slg: float | None = None
    ops: float | None = None


class PitchingStats(BaseModel):
    games: int | None = None
    wins: int | None = None
    losses: int | None = None
    innings_pitched: str | None = None
    hits: int | None = None
    runs: int | None = None
    earned_runs: int | None = None
    home_runs: int | None = None
    walks: int | None = None
    strikeouts: int | None = None
    era: float | None = None
    whip: float | None = None


class FieldingStats(BaseModel):
    games: int | None = None
    games_started: int | None = None
    innings: str | None = None
    putouts: int | None = None
    assists: int | None = None
    errors: int | None = None
    fielding_percentage: float | None = None


class TeamStats(BaseModel):
    team_id: int = Field(gt=0)
    season: int
    group: str
    stats: HittingStats | PitchingStats | FieldingStats | None


class PlayerStats(BaseModel):
    player_id: int = Field(gt=0)
    season: int
    group: str
    stats: HittingStats | PitchingStats | None
