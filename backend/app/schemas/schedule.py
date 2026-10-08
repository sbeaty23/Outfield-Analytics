from datetime import datetime

from pydantic import BaseModel, Field


class ScheduledGame(BaseModel):
    game_id: int = Field(gt=0)
    game_date: datetime
    game_type: str
    away_team_id: int
    away_team_name: str
    home_team_id: int
    home_team_name: str
    away_score: int | None = None
    home_score: int | None = None
    status: str
    venue_name: str | None = None
    probable_home_pitcher: str | None = None
    probable_away_pitcher: str | None = None


class TeamSchedule(BaseModel):
    team_id: int = Field(gt=0)
    season: int
    games: list[ScheduledGame]
