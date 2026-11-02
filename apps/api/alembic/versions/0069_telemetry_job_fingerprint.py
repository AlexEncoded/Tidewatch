"""Store request fingerprints for queued telemetry idempotency."""

from alembic import op
import sqlalchemy as sa


revision = "0069_telemetry_job_fingerprint"
down_revision = "0068_maint_notification_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("telemetry_ingestion_jobs") as batch_op:
        batch_op.add_column(
            sa.Column("idempotency_fingerprint", sa.String(length=64), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("telemetry_ingestion_jobs") as batch_op:
        batch_op.drop_column("idempotency_fingerprint")
