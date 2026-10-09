from collections.abc import Awaitable, Callable
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

type DbProbe = Callable[[], Awaitable[None]]


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def get_engine(request: Request) -> AsyncEngine:
    return cast(AsyncEngine, request.app.state.engine)


def get_db_probe(engine: Annotated[AsyncEngine, Depends(get_engine)]) -> DbProbe:
    async def probe() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    return probe
