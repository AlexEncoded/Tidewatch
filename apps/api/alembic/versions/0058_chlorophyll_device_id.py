"""Associate chlorophyll-a readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0058_chlorophyll_device_id"
down_revision = "0057_conductivity_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chlorophyll_a_readings", sa.Column("device_id", sa.String(length=100), nullable=True))
    op.create_index("ix_chlorophyll_a_readings_device_id", "chlorophyll_a_readings", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_chlorophyll_a_readings_device_id", table_name="chlorophyll_a_readings")
    op.drop_column("chlorophyll_a_readings", "device_id")
