"""Associate air temperature readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0061_air_temperature_device_id"
down_revision = "0060_humidity_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("air_temperature_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_air_temperature_readings_device_id", "air_temperature_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_air_temperature_readings_device_id", table_name="air_temperature_readings")
    op.drop_column("air_temperature_readings", "device_id")
