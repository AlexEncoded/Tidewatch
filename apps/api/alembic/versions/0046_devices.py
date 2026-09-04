"""Add physical device registry for redundant buoy units."""

from alembic import op
import sqlalchemy as sa


revision = "0046_devices"
down_revision = "0045_underwater_acoustic_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("device_id", sa.String(length=100), nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("device_id"),
        sa.UniqueConstraint("buoy_id", "sensor_channel", name="uq_devices_buoy_channel"),
    )
    op.create_index("ix_devices_buoy_id", "devices", ["buoy_id"])


def downgrade() -> None:
    op.drop_index("ix_devices_buoy_id", table_name="devices")
    op.drop_table("devices")
