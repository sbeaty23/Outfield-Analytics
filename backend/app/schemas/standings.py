from pydantic import BaseModel


class StandingEntry(BaseModel):
    team_id: int
    team_name: str
    wins: int
    losses: int
    winning_percentage: float
    games_back: str
    division_rank: int | None = None
    league_rank: int | None = None
    last_ten_wins: int | None = None
    last_ten_losses: int | None = None
    streak: str | None = None


class DivisionStandings(BaseModel):
    division_id: int
    division_name: str
    teams: list[StandingEntry]


class Standings(BaseModel):
    season: int
    divisions: list[DivisionStandings]
