import asyncio

import pytest

from obriy_api.telemetry import QUEUE_SIZE, TelemetryBroadcaster


@pytest.fixture
def broadcaster() -> TelemetryBroadcaster:
    return TelemetryBroadcaster()


def drain(q: asyncio.Queue[str]) -> list[str]:
    return [q.get_nowait() for _ in range(q.qsize())]


def test_subscribers_get_same_messages(broadcaster: TelemetryBroadcaster) -> None:
    q1, q2 = broadcaster.subscribe(), broadcaster.subscribe()

    broadcaster.publish("a")
    broadcaster.publish("b")
    broadcaster.publish("c")

    assert drain(q1) == ["a", "b", "c"]
    assert drain(q2) == ["a", "b", "c"]


def test_drop_oldest_messages(broadcaster: TelemetryBroadcaster) -> None:
    q = broadcaster.subscribe()
    n = QUEUE_SIZE + 5

    for i in range(1, n):
        broadcaster.publish(str(i))

    assert drain(q) == [str(i) for i in range(n - QUEUE_SIZE, n)]


def test_unsubscribe(broadcaster: TelemetryBroadcaster) -> None:
    q = broadcaster.subscribe()

    broadcaster.unsubscribe(q)
    broadcaster.unsubscribe(q)

    broadcaster.publish("a")

    assert q.empty()
