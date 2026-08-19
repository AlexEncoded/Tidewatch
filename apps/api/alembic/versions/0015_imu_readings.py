"""Add redundant IMU readings.

Revision ID: 0015_imu_readings
Revises: 0014_health_fallback_decisions
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_imu_readings"
down_revision = "0014_health_fallback_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "imu_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("acceleration_x_mps2", sa.Float(), nullable=False),
        sa.Column("acceleration_y_mps2", sa.Float(), nullable=False),
        sa.Column("acceleration_z_mps2", sa.Float(), nullable=False),
        sa.Column("angular_velocity_x_dps", sa.Float(), nullable=False),
        sa.Column("angular_velocity_y_dps", sa.Float(), nullable=False),
        sa.Column("angular_velocity_z_dps", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False, server_default="A"),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False, server_default="good"),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("imu_readings", "sensor_channel", server_default=None)
    op.alter_column("imu_readings", "quality", server_default=None)
    op.create_index("ix_imu_readings_buoy_id", "imu_readings", ["buoy_id"])
    op.create_index("ix_imu_readings_measured_at", "imu_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_imu_readings_measured_at", table_name="imu_readings")
    op.drop_index("ix_imu_readings_buoy_id", table_name="imu_readings")
    op.drop_table("imu_readings")
