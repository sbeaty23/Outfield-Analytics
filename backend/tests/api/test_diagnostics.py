from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api import diagnostics
from app.cache.service import CacheService
from app.core.config import settings
from app.main import create_app


def test_diagnostics_reports_dependencies_without_calling_mlb(monkeypatch) -> None:
    monkeypatch.setattr(diagnostics, "is_database_connected", lambda: True)
    status = AsyncMock(return_value="connected")
    monkeypatch.setattr(CacheService, "status", status)

    with TestClient(create_app()) as client:
        response = client.get("/api/diagnostics")

    assert response.status_code == 200
    assert response.json() == {
        "database": "connected",
        "redis": "connected",
        "mlb_provider": "configured",
    }
    assert status.await_count >= 1


def test_diagnostics_reports_degraded_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(diagnostics, "is_database_connected", lambda: False)
    monkeypatch.setattr(CacheService, "status", AsyncMock(return_value="unavailable"))

    with TestClient(create_app()) as client:
        response = client.get("/api/diagnostics")

    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"
    assert response.json()["redis"] == "unavailable"


def test_diagnostics_is_not_registered_in_production(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    application = create_app()
    assert "/api/diagnostics" not in application.openapi()["paths"]
