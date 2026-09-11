from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "not_configured",
    }


def test_unknown_route_returns_not_found() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_health_rejects_unsupported_methods() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/health")

    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def test_unexpected_errors_are_sanitized() -> None:
    application = create_app()

    @application.get("/__test/error")
    async def raise_unexpected_error() -> None:
        raise RuntimeError("sensitive internal detail")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/__test/error")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "sensitive internal detail" not in response.text
