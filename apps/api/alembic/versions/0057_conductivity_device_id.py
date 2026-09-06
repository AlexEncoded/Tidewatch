"""Associate conductivity readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0057_conductivity_device_id"
down_revision = "0056_ph_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conductivity_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_conductivity_readings_device_id", "conductivity_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_conductivity_readings_device_id", table_name="conductivity_readings")
    op.drop_column("conductivity_readings", "device_id")
