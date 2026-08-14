"""Add battery readings.

Revision ID: 0008_battery_readings
Revises: 0007_sensor_channels
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_battery_readings"
down_revision: Union[str, Sequence[str], None] = "0007_sensor_channels"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "battery_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("battery_percent", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_battery_readings_buoy_id", "battery_readings", ["buoy_id"])
    op.create_index("ix_battery_readings_measured_at", "battery_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_battery_readings_measured_at", table_name="battery_readings")
    op.drop_index("ix_battery_readings_buoy_id", table_name="battery_readings")
    op.drop_table("battery_readings")
