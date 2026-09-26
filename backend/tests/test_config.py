"""Configuration is loaded from the environment without relying on local files."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_required_environment_and_cors_origin(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://db.example.test/app")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("FRONTEND_URL", "https://frontend.test/")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://db.example.test/app"
    assert settings.environment == "test"
    assert settings.cors_origins == ["https://frontend.test"]


def test_settings_reject_missing_required_value(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("FRONTEND_URL", "https://frontend.test")

    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)
