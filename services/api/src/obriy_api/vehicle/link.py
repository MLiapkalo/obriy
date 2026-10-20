from collections.abc import AsyncIterator
from typing import Protocol

from obriy_contracts import Telemetry


class VehicleLink(Protocol):
    """The only way the API talks to a vehicle; fake and MAVLink are implementations."""

    def telemetry(self) -> AsyncIterator[Telemetry]:
        """Stream of state samples, newest last; consume with ``async for``."""
