"""Add redundant chlorophyll-a readings.

Revision ID: 0031_chlorophyll
Revises: 0030_conductivity_health
"""

from alembic import op
import sqlalchemy as sa


revision = "0031_chlorophyll"
down_revision = "0030_conductivity_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chlorophyll_a_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("chlorophyll_a_ug_l", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chlorophyll_a_readings_buoy_id", "chlorophyll_a_readings", ["buoy_id"])
    op.create_index("ix_chlorophyll_a_readings_measured_at", "chlorophyll_a_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_chlorophyll_a_readings_measured_at", table_name="chlorophyll_a_readings")
    op.drop_index("ix_chlorophyll_a_readings_buoy_id", table_name="chlorophyll_a_readings")
    op.drop_table("chlorophyll_a_readings")
