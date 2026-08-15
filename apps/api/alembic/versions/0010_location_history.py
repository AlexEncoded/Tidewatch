"""add buoy location history

Revision ID: 0010_location_history
Revises: 0009_reading_quality
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_location_history"
down_revision = "0009_reading_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "buoy_location_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_buoy_location_readings_buoy_id", "buoy_location_readings", ["buoy_id"])
    op.create_index("ix_buoy_location_readings_measured_at", "buoy_location_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_buoy_location_readings_measured_at", table_name="buoy_location_readings")
    op.drop_index("ix_buoy_location_readings_buoy_id", table_name="buoy_location_readings")
    op.drop_table("buoy_location_readings")
