"""Add salinity readings.

Revision ID: 0006_salinity_readings
Revises: 0005_pressure_readings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_salinity_readings"
down_revision: Union[str, Sequence[str], None] = "0005_pressure_readings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "salinity_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("salinity_psu", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_salinity_readings_buoy_id", "salinity_readings", ["buoy_id"])
    op.create_index("ix_salinity_readings_measured_at", "salinity_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_salinity_readings_measured_at", table_name="salinity_readings")
    op.drop_index("ix_salinity_readings_buoy_id", table_name="salinity_readings")
    op.drop_table("salinity_readings")
