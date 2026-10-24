import asyncio
import contextlib
import time
from collections.abc import AsyncGenerator, AsyncIterator

import pytest

from obriy_api.telemetry import TelemetryBroadcaster, run_reader
from obriy_api.vehicle import FakeVehicle, VehicleLink
from obriy_contracts import Telemetry, TelemetryMessage

SAMPLES = [FakeVehicle(50.45, 30.52).state_at(t) for t in (0, 10)]


class FlakyVehicle:
    def __init__(self, samples: list[Telemetry]) -> None:
        self.samples = samples
        self.calls = 0

    async def telemetry(self) -> AsyncIterator[Telemetry]:
        self.calls += 1
        match self.calls:
            case 1:
                yield self.samples[0]
                raise RuntimeError("link lost")
            case 2:
                yield self.samples[1]
                await asyncio.Event().wait()  # block forever


@pytest.fixture
def broadcaster() -> TelemetryBroadcaster:
    return TelemetryBroadcaster()


@pytest.fixture
def vehicle() -> FlakyVehicle:
    return FlakyVehicle(samples=SAMPLES)


@contextlib.asynccontextmanager
async def running(vehicle: VehicleLink, broadcaster: TelemetryBroadcaster) -> AsyncGenerator[None]:
    task = asyncio.create_task(run_reader(vehicle, broadcaster, retry_delay_s=0))
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):  # the cancelled task re-raises it on await
            await task


@pytest.mark.anyio
async def test_samples_publish(vehicle: FlakyVehicle, broadcaster: TelemetryBroadcaster) -> None:
    q = broadcaster.subscribe()
    before = time.time_ns() // 1_000_000

    async with running(vehicle=vehicle, broadcaster=broadcaster):
        raw = await asyncio.wait_for(q.get(), 1)

    after = time.time_ns() // 1_000_000
    message = TelemetryMessage.model_validate_json(raw)
    assert message.payload == SAMPLES[0]
    assert before <= message.ts <= after


@pytest.mark.anyio
async def test_recovery_when_stream_raises(vehicle: FlakyVehicle, broadcaster: TelemetryBroadcaster) -> None:
    q = broadcaster.subscribe()

    async with running(vehicle=vehicle, broadcaster=broadcaster):
        raw_first = await asyncio.wait_for(q.get(), 1)
        message_first = TelemetryMessage.model_validate_json(raw_first)

        raw_second = await asyncio.wait_for(q.get(), 1)
        message_second = TelemetryMessage.model_validate_json(raw_second)

        assert message_first.payload == SAMPLES[0]
        assert message_second.payload == SAMPLES[1]
