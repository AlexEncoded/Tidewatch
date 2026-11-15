"""Application use case for system readiness checks."""

from .system_ports import DatabaseHealthReader


def check_database_health(reader: DatabaseHealthReader) -> None:
    """Verify database availability through the system input port."""
    reader.check_database()
