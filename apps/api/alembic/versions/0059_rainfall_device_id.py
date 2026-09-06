"""Associate rainfall readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0059_rainfall_device_id"
down_revision = "0058_chlorophyll_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rainfall_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_rainfall_readings_device_id", "rainfall_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_rainfall_readings_device_id", table_name="rainfall_readings")
    op.drop_column("rainfall_readings", "device_id")
