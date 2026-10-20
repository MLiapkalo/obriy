import math

import pytest

from obriy_api.vehicle.fake import RADIUS_M, SPEED_MPS, FakeVehicle
from obriy_contracts import Telemetry

HOME_LAT, HOME_LON = 50.45, 30.52
QUARTER_LAP_S = math.pi * RADIUS_M / (2 * SPEED_MPS)


@pytest.fixture
def vehicle() -> FakeVehicle:
    return FakeVehicle(home_lat=HOME_LAT, home_lon=HOME_LON)


@pytest.mark.parametrize(
    ("t", "lat", "lon", "heading"),
    [
        pytest.param(0.0, 50.451797, HOME_LON, 90.0, id="start"),
        pytest.param(QUARTER_LAP_S, HOME_LAT, 30.522822, 180, id="quarter_lap"),
        # t = 20 s, theta = 1 rad
        pytest.param(20.0, 50.450971, 30.522374, 147.30, id="t_20s"),
    ],
)
def test_state_at_position_and_heading(vehicle: FakeVehicle, t: float, lat: float, lon: float, heading: float) -> None:
    s = vehicle.state_at(t)

    # Expected values have 6 decimals, so allow up to 1e-6 degrees (~11 cm) of rounding.
    assert s.lat == pytest.approx(lat, abs=1e-6)
    assert s.lon == pytest.approx(lon, abs=1e-6)
    assert s.heading_deg == pytest.approx(heading, abs=0.01)


@pytest.mark.parametrize(
    ("t", "pct", "v"),
    [
        pytest.param(0.0, 100, 16.8, id="cycle_start"),
        pytest.param(150.0, 60, 15.68, id="midcycle"),
        pytest.param(299.0, 20, 14.5675, id="cycle_end"),
    ],
)
def test_state_at_battery(vehicle: FakeVehicle, t: float, pct: int, v: float) -> None:
    s = vehicle.state_at(t)

    assert s.battery_remaining_pct == pct
    assert s.battery_voltage_v == pytest.approx(v, abs=1e-3)


def test_battery_cycle_restart(vehicle: FakeVehicle) -> None:
    start = vehicle.state_at(0.0)
    end = vehicle.state_at(300.0)

    assert start.battery_voltage_v == pytest.approx(end.battery_voltage_v, abs=1e-3)
    assert start.battery_remaining_pct == end.battery_remaining_pct


@pytest.mark.anyio
async def test_telemetry_yields_ordered_samples(vehicle: FakeVehicle) -> None:
    samples: list[Telemetry] = []
    async for s in vehicle.telemetry():
        samples.append(s)
        if len(samples) == 3:
            break
    assert samples[0].heading_deg < samples[1].heading_deg < samples[2].heading_deg
