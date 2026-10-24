import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI
from pydantic.json_schema import models_json_schema

from obriy_api.config import Settings
from obriy_api.db import create_engine
from obriy_api.health import router as health_router
from obriy_api.telemetry import TelemetryBroadcaster, run_reader
from obriy_api.vehicle import FakeVehicle
from obriy_contracts import TelemetryMessage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()
    engine = create_engine(settings.database_url)
    app.state.engine = engine
    broadcaster = TelemetryBroadcaster()
    app.state.broadcaster = broadcaster
    reader_task = asyncio.create_task(
        run_reader(
            vehicle=FakeVehicle(home_lat=settings.fake_home_lat, home_lon=settings.fake_home_lon),
            broadcaster=broadcaster,
        )
    )
    app.state.reader_task = reader_task
    try:
        yield
    finally:
        reader_task.cancel()
        with suppress(asyncio.CancelledError):
            await reader_task
        await engine.dispose()


class ObriyAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:
        if self.openapi_schema is None:
            schema = super().openapi()
            _, defs = models_json_schema(
                [(TelemetryMessage, "serialization")], ref_template="#/components/schemas/{model}"
            )
            schema.setdefault("components", {}).setdefault("schemas", {}).update(defs["$defs"])
        return super().openapi()


def create_app() -> FastAPI:
    app = ObriyAPI(title="Obriy API", lifespan=lifespan)
    app.include_router(health_router)
    return app
