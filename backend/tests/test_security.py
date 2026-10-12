import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security import RequestSecurityMiddleware


def test_request_rate_limit_is_bounded_per_client() -> None:
    app = FastAPI()
    app.add_middleware(RequestSecurityMiddleware, timeout=1, requests_per_minute=1)

    @app.get("/api/test")
    async def ok():
        return {"ok": True}

    with TestClient(app) as client:
        assert client.get("/api/test").status_code == 200
        response = client.get("/api/test")

    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded. Try again later."}
    assert response.headers["retry-after"] == "60"


def test_request_timeout_is_sanitized() -> None:
    app = FastAPI()
    app.add_middleware(RequestSecurityMiddleware, timeout=0.01, requests_per_minute=10)

    @app.get("/")
    async def slow():
        await asyncio.sleep(0.1)
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 504
    assert response.json() == {"detail": "Request timed out"}


def test_expensive_requests_have_a_separate_budget() -> None:
    app = FastAPI()
    app.add_middleware(
        RequestSecurityMiddleware,
        timeout=1,
        requests_per_minute=100,
        expensive_requests_per_minute=2,
    )

    @app.get("/api/teams/{team_id}")
    async def team(team_id: int):
        return {"team_id": team_id}

    with TestClient(app) as client:
        assert client.get("/api/teams/1").status_code == 200
        assert client.get("/api/teams/2").status_code == 200
        response = client.get(
            "/api/teams/3", headers={"X-Forwarded-For": "untrusted.example"}
        )

    assert response.status_code == 429


def test_rate_limit_window_resets() -> None:
    current = [0.0]
    app = FastAPI()
    app.add_middleware(
        RequestSecurityMiddleware,
        timeout=1,
        requests_per_minute=1,
        clock=lambda: current[0],
    )

    @app.get("/api/test")
    async def ok():
        return {"ok": True}

    with TestClient(app) as client:
        assert client.get("/api/test").status_code == 200
        assert client.get("/api/test").status_code == 429
        current[0] = 60.0
        assert client.get("/api/test").status_code == 200


def test_configured_general_and_expensive_boundaries() -> None:
    general = FastAPI()
    general.add_middleware(
        RequestSecurityMiddleware,
        timeout=1,
        requests_per_minute=100,
        expensive_requests_per_minute=30,
    )

    @general.get("/api/status")
    async def status():
        return {"ok": True}

    with TestClient(general) as client:
        assert all(client.get("/api/status").status_code == 200 for _ in range(100))
        assert client.get("/api/status").status_code == 429

    expensive = FastAPI()
    expensive.add_middleware(
        RequestSecurityMiddleware,
        timeout=1,
        requests_per_minute=100,
        expensive_requests_per_minute=30,
    )

    @expensive.get("/api/standings")
    async def standings():
        return {"ok": True}

    with TestClient(expensive) as client:
        assert all(client.get("/api/standings").status_code == 200 for _ in range(30))
        assert client.get("/api/standings").status_code == 429
