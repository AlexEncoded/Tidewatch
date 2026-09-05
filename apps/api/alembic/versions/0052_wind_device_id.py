"""Associate wind readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0052_wind_device_id"
down_revision = "0051_ambient_light_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("wind_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_wind_readings_device_id", "wind_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_wind_readings_device_id", table_name="wind_readings")
    op.drop_column("wind_readings", "device_id")
