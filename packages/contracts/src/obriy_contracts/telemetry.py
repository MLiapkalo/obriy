from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Telemetry(BaseModel):
    vehicle_id: str
    lat: Annotated[float, Field(ge=-90, le=90)]
    lon: Annotated[float, Field(ge=-180, le=180)]
    alt_rel_m: float
    groundspeed_mps: Annotated[float, Field(ge=0)]
    heading_deg: Annotated[float, Field(ge=0, lt=360)]
    battery_voltage_v: Annotated[float, Field(ge=0)]
    battery_remaining_pct: Annotated[int, Field(ge=0, le=100)] | None


class TelemetryMessage(BaseModel):
    type: Literal["telemetry"] = "telemetry"
    ts: Annotated[int, Field(ge=0)]
    payload: Telemetry
