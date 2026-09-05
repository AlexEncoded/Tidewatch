"""Associate GNSS positions with their physical device."""

from alembic import op
import sqlalchemy as sa


revision = "0048_location_device_id"
down_revision = "0047_device_last_seen"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("buoy_location_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_buoy_location_readings_device_id", "buoy_location_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_buoy_location_readings_device_id", table_name="buoy_location_readings")
    op.drop_column("buoy_location_readings", "device_id")
