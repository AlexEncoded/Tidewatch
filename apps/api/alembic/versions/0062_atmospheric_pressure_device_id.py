"""Associate atmospheric pressure readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0062_atmospheric_pressure_device_id"
down_revision = "0061_air_temperature_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "atmospheric_pressure_readings",
        sa.Column("device_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_atmospheric_pressure_readings_device_id",
        "atmospheric_pressure_readings",
        ["device_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_atmospheric_pressure_readings_device_id",
        table_name="atmospheric_pressure_readings",
    )
    op.drop_column("atmospheric_pressure_readings", "device_id")
