"""Create the durable maintenance notification outbox."""

from alembic import op
import sqlalchemy as sa


revision = "0068_maint_notification_jobs"
down_revision = "0067_telemetry_job_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_notification_jobs",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idempotency_key", name="uq_maintenance_notification_key"
        ),
    )
    op.create_index(
        "ix_maintenance_notification_claim",
        "maintenance_notification_jobs",
        ["status", "available_at", "created_at"],
    )
    op.create_index(
        "ix_maintenance_notification_expired",
        "maintenance_notification_jobs",
        ["status", "lease_expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_notification_expired",
        table_name="maintenance_notification_jobs",
    )
    op.drop_index(
        "ix_maintenance_notification_claim",
        table_name="maintenance_notification_jobs",
    )
    op.drop_table("maintenance_notification_jobs")
