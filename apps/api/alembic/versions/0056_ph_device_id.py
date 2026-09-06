"""Associate pH readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0056_ph_device_id"
down_revision = "0055_dissolved_oxygen_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ph_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_ph_readings_device_id", "ph_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_ph_readings_device_id", table_name="ph_readings")
    op.drop_column("ph_readings", "device_id")
