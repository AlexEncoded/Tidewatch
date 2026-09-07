"""Associate acoustic altimeter readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0063_acoustic_altimeter_id"
down_revision = "0062_atm_pressure_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "acoustic_altimeter_readings", sa.Column("device_id", sa.String(length=100), nullable=True)
    )
    op.create_index(
        "ix_acoustic_altimeter_readings_device_id",
        "acoustic_altimeter_readings",
        ["device_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_acoustic_altimeter_readings_device_id",
        table_name="acoustic_altimeter_readings",
    )
    op.drop_column("acoustic_altimeter_readings", "device_id")
