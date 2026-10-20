import pytest
from pydantic import ValidationError

from obriy_api.config import Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    for name in ("FAKE_HOME_LAT", "FAKE_HOME_LON"):
        monkeypatch.delenv(name, raising=False)


def test_settings_reads_database_url_from_environment() -> None:
    assert Settings().database_url == "postgresql+asyncpg://u:p@host:5432/db"


def test_settings_provides_default_pos() -> None:
    s = Settings()
    assert s.fake_home_lat == 50.45
    assert s.fake_home_lon == 30.52


def test_settings_reads_fake_home_pos_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_home_lat, fake_home_lon = "30.3", "-120.2"

    monkeypatch.setenv("FAKE_HOME_LAT", fake_home_lat)
    monkeypatch.setenv("FAKE_HOME_LON", fake_home_lon)

    s = Settings()
    assert s.fake_home_lat == float(fake_home_lat)
    assert s.fake_home_lon == float(fake_home_lon)


def test_settings_raises_on_out_of_range_lat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_HOME_LAT", "92.5")
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    error = exc_info.value.errors()[0]
    assert error["type"] == "less_than_equal"
    assert error["loc"] == ("fake_home_lat",)


def test_settings_raises_on_out_of_range_lon(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_HOME_LON", "-191.9")
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    error = exc_info.value.errors()[0]
    assert error["type"] == "greater_than_equal"
    assert error["loc"] == ("fake_home_lon",)
