"""Associate battery readings with registered physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0065_battery_physical_device"
down_revision = "0064_underwater_acoustic_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "battery_readings",
        sa.Column(
            "physical_device_id",
            sa.String(length=100),
            sa.ForeignKey("devices.device_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_battery_readings_physical_device_id",
        "battery_readings",
        ["physical_device_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_battery_readings_physical_device_id",
        table_name="battery_readings",
    )
    op.drop_column("battery_readings", "physical_device_id")
