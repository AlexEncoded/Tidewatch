"""Create a durable queue for asynchronous telemetry ingestion."""

from alembic import op
import sqlalchemy as sa


revision = "0066_telemetry_jobs"
down_revision = "0065_battery_physical_device"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telemetry_ingestion_jobs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column(
            "buoy_id",
            sa.String(length=32),
            sa.ForeignKey("buoys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
    )
    op.create_index(
        "ix_telemetry_ingestion_jobs_claim",
        "telemetry_ingestion_jobs",
        ["status", "available_at", "created_at"],
    )
    op.create_index(
        "ix_telemetry_ingestion_jobs_expired",
        "telemetry_ingestion_jobs",
        ["status", "lease_expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_telemetry_ingestion_jobs_expired", table_name="telemetry_ingestion_jobs"
    )
    op.drop_index(
        "ix_telemetry_ingestion_jobs_claim", table_name="telemetry_ingestion_jobs"
    )
    op.drop_table("telemetry_ingestion_jobs")
