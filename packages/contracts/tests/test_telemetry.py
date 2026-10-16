import json

import pytest
from pydantic import ValidationError

from obriy_contracts import Telemetry, TelemetryMessage


def valid_telemetry() -> dict[str, object]:
    return {
        "vehicle_id": "fake-1",
        "lat": 50.451577,
        "lon": 30.521353,
        "alt_rel_m": 50.0,
        "groundspeed_mps": 10.0,
        "heading_deg": 118.6,
        "battery_voltage_v": 16.72,
        "battery_remaining_pct": 97,
    }


def test_valid_sample_serializes() -> None:
    ts = 1_791_712_800_123
    msg = TelemetryMessage(ts=ts, payload=Telemetry.model_validate(valid_telemetry()))
    assert json.loads(msg.model_dump_json()) == {"payload": valid_telemetry(), "type": "telemetry", "ts": ts}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("heading_deg", 360),
        ("heading_deg", 400),
        ("lat", 91),
        ("lon", -181),
        ("groundspeed_mps", -1),
        ("battery_remaining_pct", 101),
    ],
)
def test_out_of_range_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Telemetry.model_validate({**valid_telemetry(), field: value})
    assert exc_info.value.errors()[0]["loc"] == (field,)


def test_negative_ts_rejected() -> None:
    payload = Telemetry.model_validate(valid_telemetry())
    with pytest.raises(ValidationError) as exc_info:
        TelemetryMessage(ts=-1, payload=payload)
    assert exc_info.value.errors()[0]["loc"] == ("ts",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("heading_deg", 0),
        ("heading_deg", 359.9),
        ("lat", 90),
        ("lat", -90),
        ("battery_remaining_pct", None),
        ("battery_remaining_pct", 0),
    ],
)
def test_boundary_values_accepted(field: str, value: object) -> None:
    t = Telemetry.model_validate({**valid_telemetry(), field: value})
    assert getattr(t, field) == value
