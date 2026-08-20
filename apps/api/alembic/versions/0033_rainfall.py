"""Add redundant rainfall readings.

Revision ID: 0033_rainfall
Revises: 0032_chlorophyll_health
"""

from alembic import op
import sqlalchemy as sa


revision = "0033_rainfall"
down_revision = "0032_chlorophyll_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rainfall_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("rainfall_mm_h", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rainfall_readings_buoy_id", "rainfall_readings", ["buoy_id"])
    op.create_index("ix_rainfall_readings_measured_at", "rainfall_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_rainfall_readings_measured_at", table_name="rainfall_readings")
    op.drop_index("ix_rainfall_readings_buoy_id", table_name="rainfall_readings")
    op.drop_table("rainfall_readings")
