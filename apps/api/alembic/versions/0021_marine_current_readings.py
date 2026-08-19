"""Add redundant marine current readings.

Revision ID: 0021_marine_current_readings
Revises: 0020_wind_health_delta
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_marine_current_readings"
down_revision = "0020_wind_health_delta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marine_current_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("current_speed_mps", sa.Float(), nullable=False),
        sa.Column("current_direction_degrees", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False, server_default="A"),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False, server_default="good"),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("marine_current_readings", "sensor_channel", server_default=None)
    op.alter_column("marine_current_readings", "quality", server_default=None)
    op.create_index("ix_marine_current_readings_buoy_id", "marine_current_readings", ["buoy_id"])
    op.create_index("ix_marine_current_readings_measured_at", "marine_current_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_marine_current_readings_measured_at", table_name="marine_current_readings")
    op.drop_index("ix_marine_current_readings_buoy_id", table_name="marine_current_readings")
    op.drop_table("marine_current_readings")
