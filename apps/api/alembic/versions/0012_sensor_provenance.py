"""Add sensor provenance metadata.

Revision ID: 0012_sensor_provenance
Revises: 0011_battery_device_id
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_sensor_provenance"
down_revision = "0011_battery_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("temperature_readings", "pressure_readings", "salinity_readings"):
        op.add_column(table, sa.Column("sensor_id", sa.String(length=100), nullable=True))
        op.add_column(
            table, sa.Column("firmware_version", sa.String(length=50), nullable=True)
        )


def downgrade() -> None:
    for table in ("salinity_readings", "pressure_readings", "temperature_readings"):
        op.drop_column(table, "firmware_version")
        op.drop_column(table, "sensor_id")
