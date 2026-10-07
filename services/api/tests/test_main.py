import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

from obriy_api.main import create_app


def test_lifespan_creates_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    app = create_app()

    with TestClient(app):
        assert isinstance(app.state.engine, AsyncEngine)
