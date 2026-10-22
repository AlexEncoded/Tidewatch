"""Application input ports for system-level health checks."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DatabaseHealthReader(Protocol):
    """Check whether the primary database can answer queries."""

    def check_database(self) -> None:
        ...
