import pytest

from obriy_api.config import Settings


def test_settings_reads_database_url_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    assert Settings().database_url == "postgresql+asyncpg://u:p@host:5432/db"
