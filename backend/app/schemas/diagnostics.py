from typing import Literal

from pydantic import BaseModel


class DiagnosticsResponse(BaseModel):
    database: Literal["connected", "unavailable"]
    redis: Literal["connected", "unavailable", "disabled"]
    mlb_provider: Literal["configured"]
