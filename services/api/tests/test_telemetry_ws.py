import asyncio
import time
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from obriy_api.telemetry import TelemetryBroadcaster, router, run_reader
from obriy_api.vehicle import FakeVehicle
from obriy_contracts import Telemetry
from obriy_contracts.telemetry import TelemetryMessage

URL = "/api/ws/telemetry"
SAMPLES = [FakeVehicle(50.45, 30.52).state_at(t) for t in (0, 10)]


class ScriptedVehicle:
    def __init__(self, broadcaster: TelemetryBroadcaster, subscribers: int) -> None:
        self.broadcaster = broadcaster
        self.subscribers = subscribers

    async def telemetry(self) -> AsyncIterator[Telemetry]:
        while self.broadcaster.subscriber_count < self.subscribers:  # noqa: ASYNC110
            await asyncio.sleep(0.001)
        for s in SAMPLES:
            yield s
        await asyncio.Event().wait()


def make_app(subscribers: int) -> tuple[FastAPI, TelemetryBroadcaster]:
    broadcaster = TelemetryBroadcaster()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.broadcaster = broadcaster
        reader_task = asyncio.create_task(
            run_reader(ScriptedVehicle(broadcaster, subscribers), broadcaster=broadcaster, retry_delay_s=0)
        )
        try:
            yield
        finally:
            reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await reader_task

    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app, broadcaster


def wait_until(condition: Callable[[], bool], timeout_s: float = 1.0) -> None:
    deadline = time.monotonic() + timeout_s
    while not condition():
        assert time.monotonic() < deadline, "condition not met in time"
        time.sleep(0.001)


def read_payloads(ws: WebSocketTestSession) -> list[Telemetry]:
    return [TelemetryMessage.model_validate_json(ws.receive_text()).payload for _ in range(len(SAMPLES))]


def test_two_clients_receive_same_messages() -> None:
    app, broadcaster = make_app(subscribers=2)
    with TestClient(app) as client, client.websocket_connect(URL) as a, client.websocket_connect(URL) as b:
        assert read_payloads(a) == SAMPLES
        assert read_payloads(b) == SAMPLES
        a.close()
        b.close()
        wait_until(lambda: broadcaster.subscriber_count == 0)


def test_disconnect_removes_subscription() -> None:
    app, broadcaster = make_app(subscribers=1)
    with TestClient(app) as client, client.websocket_connect(URL) as ws:
        ws.receive_text()
        assert broadcaster.subscriber_count == 1
        ws.close()
        wait_until(lambda: broadcaster.subscriber_count == 0)
