import asyncio

QUEUE_SIZE = 10


class TelemetryBroadcaster:
    def __init__(self) -> None:
        self._queues: set[asyncio.Queue[str]] = set()

    def subscribe(self) -> asyncio.Queue[str]:
        queue = asyncio.Queue[str](maxsize=QUEUE_SIZE)
        self._queues.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        self._queues.discard(queue)

    def publish(self, message_json: str) -> None:
        for q in self._queues:
            if q.full():
                q.get_nowait()
            q.put_nowait(message_json)
