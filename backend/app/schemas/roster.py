from typing import Literal

from pydantic import BaseModel, Field


class RosterPlayer(BaseModel):
    player_id: int = Field(gt=0)
    full_name: str
    jersey_number: str | None = None
    position_name: str | None = None
    position_abbreviation: str | None = None
    position_type: str | None = None
    status: str | None = None


class Roster(BaseModel):
    team_id: int = Field(gt=0)
    season: int
    roster_type: Literal["active"] = "active"
    players: list[RosterPlayer]
