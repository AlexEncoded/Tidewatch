"""Persist sensor health checks.

Revision ID: 0013_sensor_health_history
Revises: 0012_sensor_provenance
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_sensor_health_history"
down_revision = "0012_sensor_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sensor_health_checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("temperature_delta_celsius", sa.Float(), nullable=True),
        sa.Column("pressure_delta_kpa", sa.Float(), nullable=True),
        sa.Column("salinity_delta_psu", sa.Float(), nullable=True),
        sa.Column("degraded_sensors", sa.JSON(), nullable=False),
        sa.Column("missing_sensors", sa.JSON(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_health_checks_buoy_id", "sensor_health_checks", ["buoy_id"])
    op.create_index(
        "ix_sensor_health_checks_checked_at", "sensor_health_checks", ["checked_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_health_checks_checked_at", table_name="sensor_health_checks")
    op.drop_index("ix_sensor_health_checks_buoy_id", table_name="sensor_health_checks")
    op.drop_table("sensor_health_checks")
