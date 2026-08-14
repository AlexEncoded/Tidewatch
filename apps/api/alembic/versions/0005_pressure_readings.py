"""Add pressure readings for sea-state monitoring.

Revision ID: 0005_pressure_readings
Revises: 0004_buoy_operational_status
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_pressure_readings"
down_revision: Union[str, Sequence[str], None] = "0004_buoy_operational_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pressure_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("pressure_kpa", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pressure_readings_buoy_id", "pressure_readings", ["buoy_id"])
    op.create_index("ix_pressure_readings_measured_at", "pressure_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_pressure_readings_measured_at", table_name="pressure_readings")
    op.drop_index("ix_pressure_readings_buoy_id", table_name="pressure_readings")
    op.drop_table("pressure_readings")
