import logging

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import session
from app.main import create_app


def test_database_outage_is_sanitized_and_logged(monkeypatch, caplog) -> None:
    def fail_connection():
        raise OperationalError("SELECT 1", {}, Exception("private-database-secret"))

    monkeypatch.setattr(session.engine, "connect", fail_connection)
    with (
        caplog.at_level(logging.INFO, logger="app"),
        TestClient(create_app()) as client,
    ):
        response = client.get("/api/health?token=private-query-secret")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
    assert "application started" in caplog.text
    assert "Request received method=GET" in caplog.text
    assert "Database health check failed: OperationalError" in caplog.text
    assert "route=/health status=503" in caplog.text
    assert "private-query-secret" not in caplog.text
    assert "private-database-secret" not in caplog.text + response.text


def test_successful_database_connection_is_logged(monkeypatch, caplog) -> None:
    from unittest.mock import MagicMock

    connection = MagicMock()
    monkeypatch.setattr(session.engine, "connect", connection)
    with (
        caplog.at_level(logging.INFO, logger="app"),
        TestClient(create_app()) as client,
    ):
        response = client.get("/api/health")

    assert response.status_code == 200
    connection.return_value.__enter__.return_value.execute.assert_called_once()
    assert "Database connection successful" in caplog.text
    assert "status=200" in caplog.text


def test_error_response_has_cors_and_logs_status(caplog) -> None:
    app = create_app()

    @app.get("/__test/error")
    def fail():
        raise RuntimeError("private-error-secret")

    with caplog.at_level(logging.INFO, logger="app"), TestClient(app) as client:
        response = client.get(
            "/__test/error", headers={"Origin": "http://frontend.test"}
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers["access-control-allow-origin"] == "http://frontend.test"
    assert "type=RuntimeError" in caplog.text
    assert "status=500" in caplog.text
    assert "private-error-secret" not in response.text + caplog.text


def test_validation_does_not_echo_input() -> None:
    app = create_app()

    @app.get("/__test/validate")
    def validate(count: int):
        return {"count": count}

    with TestClient(app) as client:
        response = client.get("/__test/validate?count=private-input-secret")

    assert response.status_code == 422
    assert response.json() == {"detail": "Request validation failed"}
