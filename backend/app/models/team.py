from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    mlb_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    location_name: Mapped[str] = mapped_column(String(100))
    team_name: Mapped[str | None] = mapped_column(String(100))
    abbreviation: Mapped[str] = mapped_column(String(8))
    league_id: Mapped[int | None] = mapped_column(Integer)
    league_name: Mapped[str] = mapped_column(String(100))
    division_id: Mapped[int | None] = mapped_column(Integer)
    division_name: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
