"""Create initial Tidewatch schema.

Revision ID: 0001_initial_schema
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buoys",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "temperature_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("temperature_celsius", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_temperature_readings_buoy_id", "temperature_readings", ["buoy_id"])
    op.create_index("ix_temperature_readings_measured_at", "temperature_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_temperature_readings_measured_at", table_name="temperature_readings")
    op.drop_index("ix_temperature_readings_buoy_id", table_name="temperature_readings")
    op.drop_table("temperature_readings")
    op.drop_table("buoys")
