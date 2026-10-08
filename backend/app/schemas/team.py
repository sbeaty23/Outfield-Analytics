from pydantic import BaseModel, Field


class Team(BaseModel):
    id: int = Field(gt=0)
    name: str
    abbreviation: str
    location: str
    team_name: str | None = None
    league_id: int | None = None
    league: str
    division_id: int | None = None
    division: str | None = None
    venue: str | None = None
    active: bool


class TeamList(BaseModel):
    season: int
    teams: list[Team]
