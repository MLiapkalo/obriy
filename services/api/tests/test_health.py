import asyncio

from fastapi.testclient import TestClient

from obriy_api.db import get_db_probe
from obriy_api.health import get_db_check_timeout
from obriy_api.main import create_app


def test_live_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_degraded_when_db_connection_fails() -> None:
    app = create_app()

    async def failing_probe() -> None:
        raise ConnectionRefusedError()

    app.dependency_overrides[get_db_probe] = lambda: failing_probe
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 503

    body = response.json()

    assert body["status"] == "degraded"
    assert body["checks"]["db"]["status"] == "error"
    assert body["checks"]["db"]["latency_ms"] >= 0.0
    assert "ConnectionRefusedError" in body["checks"]["db"]["detail"]


def test_ready_returns_degraded_when_db_connection_times_out() -> None:
    app = create_app()

    async def slow_probe() -> None:
        await asyncio.sleep(0.5)

    app.dependency_overrides[get_db_probe] = lambda: slow_probe
    app.dependency_overrides[get_db_check_timeout] = lambda: 0.01
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 503

    body = response.json()

    assert body["status"] == "degraded"
    assert body["checks"]["db"]["status"] == "error"
    assert body["checks"]["db"]["latency_ms"] >= 10
    assert "timed out" in body["checks"]["db"]["detail"]


def test_ready_returns_ok_when_db_connection_succeeds() -> None:
    app = create_app()

    async def successful_probe() -> None:
        return None

    app.dependency_overrides[get_db_probe] = lambda: successful_probe
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["checks"]["db"]["status"] == "ok"
    assert body["checks"]["db"]["latency_ms"] >= 0.0
    assert body["checks"]["db"]["detail"] is None
