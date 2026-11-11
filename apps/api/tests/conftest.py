"""Keep local pytest runs isolated from stale SQLite development databases."""

import os
import shutil
import sys
import tempfile
from pathlib import Path


_test_database_directory: Path | None = None
if not os.getenv("DATABASE_URL") and not os.getenv("DATABASE_URL_FILE"):
    _test_database_directory = Path(
        tempfile.mkdtemp(prefix="tidewatch-pytest-")
    ).resolve()
    database_path = (_test_database_directory / "tidewatch.db").as_posix()
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"


def pytest_unconfigure(config) -> None:
    if _test_database_directory is None:
        return

    database_module = sys.modules.get("app.database")
    if database_module is not None:
        database_module.engine.dispose()

    temp_root = Path(tempfile.gettempdir()).resolve()
    if (
        _test_database_directory.parent != temp_root
        or not _test_database_directory.name.startswith("tidewatch-pytest-")
    ):
        raise RuntimeError("Refusing to remove an unexpected pytest database directory")
    shutil.rmtree(_test_database_directory)
