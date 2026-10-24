import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

from obriy_api.main import create_app
from obriy_api.telemetry import TelemetryBroadcaster


def test_lifespan_manages_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    app = create_app()

    with TestClient(app):
        assert isinstance(app.state.engine, AsyncEngine)
        assert isinstance(app.state.broadcaster, TelemetryBroadcaster)
        assert not app.state.reader_task.done()

    assert app.state.reader_task.cancelled()
