import asyncio

import pytest
from fastapi.testclient import TestClient

from obriy_api.db import DbProbe, get_db_probe
from obriy_api.health import get_db_check_timeout
from obriy_api.main import create_app


async def ok_probe() -> None:
    return None


async def refused_probe() -> None:
    raise ConnectionRefusedError


async def slow_probe() -> None:
    await asyncio.sleep(0.5)


def client_with(probe: DbProbe, timeout_s: float = 0.01) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_probe] = lambda: probe
    app.dependency_overrides[get_db_check_timeout] = lambda: timeout_s
    return TestClient(app)


def test_live_returns_ok() -> None:
    response = TestClient(create_app()).get("/api/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_when_db_probe_succeeds() -> None:
    response = client_with(ok_probe).get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["checks"]["db"].pop("latency_ms") >= 0
    assert body == {"status": "ok", "checks": {"db": {"status": "ok", "detail": None}}}


@pytest.mark.parametrize(
    ("probe", "detail"),
    [
        (refused_probe, "ConnectionRefusedError"),
        (slow_probe, "timed out after 0.01s"),
    ],
)
def test_ready_returns_degraded_when_db_probe_fails(probe: DbProbe, detail: str) -> None:
    response = client_with(probe).get("/api/health")

    assert response.status_code == 503
    body = response.json()
    assert body["checks"]["db"].pop("latency_ms") >= 0
    assert body == {"status": "degraded", "checks": {"db": {"status": "error", "detail": detail}}}
