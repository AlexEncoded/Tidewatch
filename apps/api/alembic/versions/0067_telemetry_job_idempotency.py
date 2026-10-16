"""Make queued telemetry submissions idempotent per buoy."""

from alembic import op
import sqlalchemy as sa


revision = "0067_telemetry_job_idempotency"
down_revision = "0066_telemetry_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("telemetry_ingestion_jobs") as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint(
            "uq_telemetry_job_buoy_idempotency", ["buoy_id", "idempotency_key"]
        )


def downgrade() -> None:
    with op.batch_alter_table("telemetry_ingestion_jobs") as batch_op:
        batch_op.drop_constraint(
            "uq_telemetry_job_buoy_idempotency", type_="unique"
        )
        batch_op.drop_column("idempotency_key")
