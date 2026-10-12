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
    assert settings.allowed_hosts == ["testserver", "localhost"]


def test_settings_reject_missing_required_value(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("FRONTEND_URL", "https://frontend.test")

    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)


def test_mlb_connection_has_no_default(monkeypatch) -> None:
    monkeypatch.delenv("MLB_API_BASE_URL", raising=False)
    with pytest.raises(ValidationError, match="mlb_api_base_url"):
        Settings(_env_file=None)


def test_mlb_configuration_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("MLB_API_BASE_URL", "https://baseball.test/api/v1")
    monkeypatch.setenv("MLB_SPORT_ID", "1")
    monkeypatch.setenv("MLB_CURRENT_SEASON", "2026")
    monkeypatch.setenv("MLB_REQUEST_TIMEOUT_SECONDS", "8")
    settings = Settings(_env_file=None)
    assert str(settings.mlb_api_base_url) == "https://baseball.test/api/v1"
    assert settings.mlb_sport_id == 1
    assert settings.mlb_current_season == 2026
    assert settings.mlb_request_timeout_seconds == 8


def test_allowed_hosts_must_not_be_empty(monkeypatch) -> None:
    monkeypatch.setenv("BACKEND_ALLOWED_HOSTS", " , ")
    with pytest.raises(ValueError, match="at least one host"):
        Settings(_env_file=None).allowed_hosts


def test_cache_can_be_disabled_without_a_redis_url(monkeypatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    settings = Settings(_env_file=None, cache_enabled=False)
    assert settings.redis_url is None


def test_enabled_cache_requires_a_redis_url(monkeypatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    with pytest.raises(ValidationError, match="REDIS_URL"):
        Settings(_env_file=None, cache_enabled=True)


def test_redis_and_retry_configuration(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        cache_enabled=True,
        redis_url="redis://cache.example.test",
        redis_connect_timeout_seconds=2,
        redis_operation_timeout_seconds=3,
        redis_max_connections=12,
        mlb_max_attempts=3,
        mlb_retry_backoff_seconds=0.5,
        expensive_request_rate_limit_per_minute=30,
    )
    assert settings.cache_enabled is True
    assert settings.redis_max_connections == 12
    assert settings.mlb_max_attempts == 3


@pytest.mark.parametrize(
    "field, value",
    [
        ("mlb_api_base_url", "not-a-url"),
        ("mlb_sport_id", 11),
        ("mlb_current_season", 0),
        ("mlb_current_season", "invalid"),
        ("mlb_request_timeout_seconds", 0),
        ("mlb_request_timeout_seconds", -1),
        ("mlb_request_timeout_seconds", float("inf")),
    ],
)
def test_invalid_mlb_configuration(field, value) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})
