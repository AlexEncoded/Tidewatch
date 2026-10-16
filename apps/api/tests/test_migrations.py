from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
)


def test_alembic_revision_identifiers_fit_version_column() -> None:
    api_root = Path(__file__).parents[1]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "alembic"))
    script = ScriptDirectory.from_config(config)

    revisions = list(script.walk_revisions())
    identifiers = [revision.revision for revision in revisions]
    identifiers.extend(
        revision.down_revision
        for revision in revisions
        if isinstance(revision.down_revision, str)
    )

    assert identifiers
    assert all(len(identifier) <= 32 for identifier in identifiers)


def test_telemetry_job_idempotency_migration_upgrades_existing_queue(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "migration.sqlite"
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    metadata = MetaData()
    Table("buoys", metadata, Column("id", String(32), primary_key=True))
    jobs = Table(
        "telemetry_ingestion_jobs",
        metadata,
        Column("id", String(32), primary_key=True),
        Column("buoy_id", String(32), ForeignKey("buoys.id", ondelete="CASCADE"), nullable=False),
        Column("payload", JSON, nullable=False),
        Column("status", String(20), nullable=False),
        Column("attempts", Integer, nullable=False),
        Column("available_at", DateTime(timezone=True), nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("started_at", DateTime(timezone=True)),
        Column("completed_at", DateTime(timezone=True)),
        Column("lease_expires_at", DateTime(timezone=True)),
        Column("last_error", String(1000)),
    )
    Index("ix_telemetry_ingestion_jobs_claim", jobs.c.status, jobs.c.available_at, jobs.c.created_at)
    Index("ix_telemetry_ingestion_jobs_expired", jobs.c.status, jobs.c.lease_expires_at)
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
        connection.exec_driver_sql(
            "INSERT INTO alembic_version (version_num) VALUES ('0066_telemetry_jobs')"
        )

    api_root = Path(__file__).parents[1]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "alembic"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")

    command.upgrade(config, "head")

    inspector = inspect(engine)
    assert "idempotency_key" in {
        column["name"] for column in inspector.get_columns("telemetry_ingestion_jobs")
    }
    assert any(
        constraint["name"] == "uq_telemetry_job_buoy_idempotency"
        for constraint in inspector.get_unique_constraints("telemetry_ingestion_jobs")
    )
    engine.dispose()
