import asyncio
import logging
import time

from obriy_api.telemetry.broadcaster import TelemetryBroadcaster
from obriy_api.vehicle import VehicleLink
from obriy_contracts import TelemetryMessage

logger = logging.getLogger(__name__)

RETRY_DELAY_S = 1.0


async def run_reader(
    vehicle: VehicleLink, broadcaster: TelemetryBroadcaster, retry_delay_s: float = RETRY_DELAY_S
) -> None:
    while True:
        try:
            async for sample in vehicle.telemetry():
                tm = TelemetryMessage(ts=time.time_ns() // 1_000_000, payload=sample)
                broadcaster.publish(tm.model_dump_json())
        except Exception:
            logger.exception("Telemetry reading error")
        await asyncio.sleep(retry_delay_s)
