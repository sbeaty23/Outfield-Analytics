import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security import RequestSecurityMiddleware


def test_request_rate_limit_is_bounded_per_client() -> None:
    app = FastAPI()
    app.add_middleware(RequestSecurityMiddleware, timeout=1, requests_per_minute=1)

    @app.get("/")
    async def ok():
        return {"ok": True}

    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        response = client.get("/")

    assert response.status_code == 429
    assert response.json() == {"detail": "Too many requests"}
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
