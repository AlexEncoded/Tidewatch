"""Associate atmospheric pressure readings with physical devices."""

from alembic import op
import sqlalchemy as sa


revision = "0062_atmospheric_pressure_device_id"
down_revision = "0061_air_temperature_device_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("atmospheric_pressure_readings")}
    if "device_id" not in columns:
        op.add_column(
            "atmospheric_pressure_readings",
            sa.Column("device_id", sa.String(length=100), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("atmospheric_pressure_readings", "device_id")
