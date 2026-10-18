"""SQLAlchemy adapter for atomic telemetry batch operations."""

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class SQLAlchemyTelemetryBatchUnitOfWork:
    """Defer repository commits until a whole telemetry operation succeeds."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_atomically(self, action: Callable[[], T]) -> T:
        was_deferred = self.db.info.get("tidewatch_defer_repository_commits", False)
        self.db.info["tidewatch_defer_repository_commits"] = True
        try:
            result = action()
            if not was_deferred:
                self.db.info["tidewatch_defer_repository_commits"] = False
                self.db.commit()
            return result
        except Exception:
            if not was_deferred:
                self.db.rollback()
            raise
        finally:
            if was_deferred:
                self.db.info["tidewatch_defer_repository_commits"] = True
            else:
                self.db.info.pop("tidewatch_defer_repository_commits", None)
