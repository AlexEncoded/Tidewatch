"""Store IMU acceleration delta in sensor health history.

Revision ID: 0016_imu_health_delta
Revises: 0015_imu_readings
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_imu_health_delta"
down_revision = "0015_imu_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("imu_acceleration_delta_mps2", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "imu_acceleration_delta_mps2")
