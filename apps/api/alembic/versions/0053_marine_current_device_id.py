"""Associate marine current readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0053_marine_current_device_id"
down_revision = "0052_wind_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "marine_current_readings", sa.Column("device_id", sa.String(length=100), nullable=True)
    )
    op.create_index("ix_marine_current_readings_device_id", "marine_current_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_marine_current_readings_device_id", table_name="marine_current_readings")
    op.drop_column("marine_current_readings", "device_id")
