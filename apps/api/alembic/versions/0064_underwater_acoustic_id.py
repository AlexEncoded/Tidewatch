"""Associate underwater acoustic readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0064_underwater_acoustic_id"
down_revision = "0063_acoustic_altimeter_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "underwater_acoustic_readings",
        sa.Column("device_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_underwater_acoustic_readings_device_id",
        "underwater_acoustic_readings",
        ["device_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_underwater_acoustic_readings_device_id",
        table_name="underwater_acoustic_readings",
    )
    op.drop_column("underwater_acoustic_readings", "device_id")
