"""Associate dissolved oxygen readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0055_dissolved_oxygen_device_id"
down_revision = "0054_turbidity_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "dissolved_oxygen_readings", sa.Column("device_id", sa.String(length=100), nullable=True)
    )
    op.create_index("ix_dissolved_oxygen_readings_device_id", "dissolved_oxygen_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_dissolved_oxygen_readings_device_id", table_name="dissolved_oxygen_readings")
    op.drop_column("dissolved_oxygen_readings", "device_id")
