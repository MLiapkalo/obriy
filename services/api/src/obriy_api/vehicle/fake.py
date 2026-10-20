import asyncio
import math
import time
from collections.abc import AsyncIterator

from obriy_contracts import Telemetry

RADIUS_M = 200.0
M_PER_DEG_LAT = 111_320.0
VEHICLE_ID = "fake-1"
ALT_M = 50.0
SPEED_MPS = 10.0

BATTERY_CYCLE_S = 300.0
BATTERY_FULL_PCT = 100.0
BATTERY_DRAIN_PCT = 80.0
BATTERY_EMPTY_V = 14.0
BATTERY_FULL_V = 16.8

RATE_HZ = 10.0


class FakeVehicle:
    def __init__(self, home_lat: float, home_lon: float) -> None:
        self.home_lat = home_lat
        self.home_lon = home_lon

    async def telemetry(self) -> AsyncIterator[Telemetry]:
        start = time.monotonic()
        while True:
            yield self.state_at(time.monotonic() - start)
            await asyncio.sleep(1 / RATE_HZ)

    def state_at(self, t: float) -> Telemetry:
        d = SPEED_MPS * t
        theta = d / RADIUS_M
        north = RADIUS_M * math.cos(theta)
        east = RADIUS_M * math.sin(theta)
        # a battery that drains for BATTERY_DRAIN_PCT over BATTERY_CYCLE_S
        # remaining = BATTERY_FULL_PCT - drained, where drained = BATTERY_DRAIN_PCT * fraction of the cycle done
        pct = BATTERY_FULL_PCT - BATTERY_DRAIN_PCT * (t % BATTERY_CYCLE_S) / BATTERY_CYCLE_S

        return Telemetry(
            vehicle_id=VEHICLE_ID,
            lat=self.home_lat + north / M_PER_DEG_LAT,
            lon=self.home_lon + east / (M_PER_DEG_LAT * math.cos(math.radians(self.home_lat))),
            alt_rel_m=ALT_M,
            groundspeed_mps=SPEED_MPS,
            heading_deg=(math.degrees(theta) + 90) % 360,
            # battery voltage at 0% - BATTERY_EMPTY_V, at 100% - BATTERY_FULL_V
            # BATTERY_FULL_V - BATTERY_EMPTY_V is a width of range between empty and full
            battery_voltage_v=BATTERY_EMPTY_V + (BATTERY_FULL_V - BATTERY_EMPTY_V) * pct / BATTERY_FULL_PCT,
            battery_remaining_pct=round(pct),
        )
