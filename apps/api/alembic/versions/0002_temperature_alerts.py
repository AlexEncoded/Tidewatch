"""Add persistent temperature alerts.

Revision ID: 0002_temperature_alerts
Revises: 0001_initial_schema
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_temperature_alerts"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "temperature_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("reading_measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("temperature_celsius", sa.Float(), nullable=False),
        sa.Column("average_temperature", sa.Float(), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("buoy_id", "reading_measured_at"),
    )
    op.create_index("ix_temperature_alerts_buoy_id", "temperature_alerts", ["buoy_id"])


def downgrade() -> None:
    op.drop_index("ix_temperature_alerts_buoy_id", table_name="temperature_alerts")
    op.drop_table("temperature_alerts")
