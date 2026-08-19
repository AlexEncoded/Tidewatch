"""Add redundant pH readings.

Revision ID: 0027_ph_readings
Revises: 0026_do_health_delta
"""

from alembic import op
import sqlalchemy as sa


revision = "0027_ph_readings"
down_revision = "0026_do_health_delta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ph_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("ph", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ph_readings_buoy_id", "ph_readings", ["buoy_id"])
    op.create_index("ix_ph_readings_measured_at", "ph_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_ph_readings_measured_at", table_name="ph_readings")
    op.drop_index("ix_ph_readings_buoy_id", table_name="ph_readings")
    op.drop_table("ph_readings")
