"""Typed application configuration loaded from the environment."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    database_read_only: bool = True
    environment: Literal["development", "test", "production"]
    frontend_url: AnyHttpUrl
    backend_allowed_hosts: str
    request_timeout_seconds: float = Field(default=20, gt=0, le=60)
    request_rate_limit_per_minute: int = Field(default=120, ge=1, le=10_000)
    mlb_api_base_url: AnyHttpUrl
    mlb_sport_id: int = Field(default=1, ge=1, le=1)
    mlb_current_season: int = Field(
        default_factory=lambda: datetime.now(UTC).year, ge=1876, le=9999
    )
    mlb_request_timeout_seconds: float = Field(default=10, gt=0, le=60)
    mlb_max_concurrent_requests: int = Field(default=8, ge=1, le=64)
    mlb_max_response_bytes: int = Field(default=2_000_000, ge=1024, le=10_000_000)

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [str(self.frontend_url).rstrip("/")]

    @property
    def allowed_hosts(self) -> list[str]:
        hosts = [
            host.strip().lower()
            for host in self.backend_allowed_hosts.split(",")
            if host.strip()
        ]
        if not hosts:
            raise ValueError("BACKEND_ALLOWED_HOSTS must contain at least one host")
        return hosts


settings = Settings()

APP_TITLE = "Outfield Analytics API"
APP_VERSION = "0.2.0"
