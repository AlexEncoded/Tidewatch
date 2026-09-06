"""Associate humidity readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0060_humidity_device_id"
down_revision = "0059_rainfall_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("humidity_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_humidity_readings_device_id", "humidity_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_humidity_readings_device_id", table_name="humidity_readings")
    op.drop_column("humidity_readings", "device_id")
