"""Associate core redundant sensor readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0050_core_reading_device_id"
down_revision = "0049_imu_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("temperature_readings", "pressure_readings", "salinity_readings"):
        op.add_column(table, sa.Column("device_id", sa.String(length=100), nullable=True))
        op.create_index(f"ix_{table}_device_id", table, ["device_id"])


def downgrade() -> None:
    for table in ("salinity_readings", "pressure_readings", "temperature_readings"):
        op.drop_index(f"ix_{table}_device_id", table_name=table)
        op.drop_column(table, "device_id")
