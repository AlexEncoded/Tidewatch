"""Add quality metadata to sensor readings.

Revision ID: 0009_reading_quality
Revises: 0008_battery_readings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_reading_quality"
down_revision: Union[str, Sequence[str], None] = "0008_battery_readings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("temperature_readings", "pressure_readings", "salinity_readings"):
        op.add_column(
            table,
            sa.Column("quality", sa.String(length=12), nullable=False, server_default="good"),
        )
        op.alter_column(table, "quality", server_default=None)


def downgrade() -> None:
    for table in ("salinity_readings", "pressure_readings", "temperature_readings"):
        op.drop_column(table, "quality")
