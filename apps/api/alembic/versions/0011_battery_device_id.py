"""identify redundant battery units

Revision ID: 0011_battery_device_id
Revises: 0010_location_history
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_battery_device_id"
down_revision = "0010_location_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "battery_readings",
        sa.Column("device_id", sa.String(length=1), nullable=False, server_default="A"),
    )
    op.create_index(
        "ix_battery_readings_device_id", "battery_readings", ["device_id"]
    )
    op.alter_column("battery_readings", "device_id", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_battery_readings_device_id", table_name="battery_readings")
    op.drop_column("battery_readings", "device_id")
