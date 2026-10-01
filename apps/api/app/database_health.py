"""SQL adapter for the application database-health port."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from .application.ports import DatabaseHealthReader


class SQLDatabaseHealthReader(DatabaseHealthReader):
    """Verify database connectivity with a lightweight query."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def check_database(self) -> None:
        self._db.execute(text("SELECT 1"))
