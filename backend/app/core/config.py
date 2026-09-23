"""Typed application configuration loaded from the environment."""

from typing import Literal

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    environment: Literal["development", "test", "production"]
    frontend_url: AnyHttpUrl

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [str(self.frontend_url).rstrip("/")]


settings = Settings()

APP_TITLE = "Outfield Analytics API"
APP_VERSION = "0.1.0"
