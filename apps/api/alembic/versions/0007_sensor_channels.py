"""Add A/B channels for redundant buoy sensors.

Revision ID: 0007_sensor_channels
Revises: 0006_salinity_readings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_sensor_channels"
down_revision: Union[str, Sequence[str], None] = "0006_salinity_readings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("temperature_readings", "pressure_readings", "salinity_readings"):
        op.add_column(
            table,
            sa.Column("sensor_channel", sa.String(length=1), nullable=False, server_default="A"),
        )
        op.alter_column(table, "sensor_channel", server_default=None)


def downgrade() -> None:
    for table in ("salinity_readings", "pressure_readings", "temperature_readings"):
        op.drop_column(table, "sensor_channel")
