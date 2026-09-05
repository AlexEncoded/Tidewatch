"""Associate IMU readings with their physical device."""

from alembic import op
import sqlalchemy as sa


revision = "0049_imu_device_id"
down_revision = "0048_location_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("imu_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_imu_readings_device_id", "imu_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_imu_readings_device_id", table_name="imu_readings")
    op.drop_column("imu_readings", "device_id")
