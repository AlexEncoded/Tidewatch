"""Add redundant anemometer and wind vane readings.

Revision ID: 0019_wind_readings
Revises: 0018_ambient_light_health_delta
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_wind_readings"
down_revision = "0018_ambient_light_health_delta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wind_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("wind_speed_mps", sa.Float(), nullable=False),
        sa.Column("wind_direction_degrees", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False, server_default="A"),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False, server_default="good"),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("wind_readings", "sensor_channel", server_default=None)
    op.alter_column("wind_readings", "quality", server_default=None)
    op.create_index("ix_wind_readings_buoy_id", "wind_readings", ["buoy_id"])
    op.create_index("ix_wind_readings_measured_at", "wind_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_wind_readings_measured_at", table_name="wind_readings")
    op.drop_index("ix_wind_readings_buoy_id", table_name="wind_readings")
    op.drop_table("wind_readings")
