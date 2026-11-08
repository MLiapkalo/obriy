import asyncio
from typing import Annotated, cast

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.requests import HTTPConnection

from obriy_api.telemetry.broadcaster import TelemetryBroadcaster


def get_broadcaster(conn: HTTPConnection) -> TelemetryBroadcaster:
    return cast(TelemetryBroadcaster, conn.app.state.broadcaster)


async def _send_loop(websocket: WebSocket, queue: asyncio.Queue[str]) -> None:
    while True:
        await websocket.send_text(await queue.get())


async def _receive_loop(websocket: WebSocket) -> None:
    while True:
        await websocket.receive_text()


router = APIRouter(prefix="/api/ws", tags=["telemetry"])


@router.websocket("/telemetry")
async def telemetry_ws(
    websocket: WebSocket, broadcaster: Annotated[TelemetryBroadcaster, Depends(get_broadcaster)]
) -> None:
    await websocket.accept()
    queue = broadcaster.subscribe()
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(_send_loop(websocket, queue))
            tg.create_task(_receive_loop(websocket))
    except* WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe(queue)
