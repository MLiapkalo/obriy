from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from obriy_api.config import Settings
from obriy_api.db import create_engine
from obriy_api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()
    engine = create_engine(settings.database_url)
    app.state.engine = engine
    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Obriy API", lifespan=lifespan)
    app.include_router(health_router)
    return app
