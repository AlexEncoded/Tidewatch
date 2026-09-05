"""Associate ambient light readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0051_ambient_light_device_id"
down_revision = "0050_core_reading_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ambient_light_readings", sa.Column("device_id", sa.String(length=100), nullable=True)
    )
    op.create_index("ix_ambient_light_readings_device_id", "ambient_light_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_ambient_light_readings_device_id", table_name="ambient_light_readings")
    op.drop_column("ambient_light_readings", "device_id")
