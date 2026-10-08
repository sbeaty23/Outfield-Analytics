from pydantic import BaseModel, Field


class Player(BaseModel):
    id: int = Field(gt=0)
    full_name: str
    first_name: str | None = None
    last_name: str | None = None
    jersey_number: str | None = None
    primary_position: str | None = None
    bat_side: str | None = None
    throw_side: str | None = None
    height: str | None = None
    weight: int | None = None
    active: bool
    current_team_id: int | None = None
