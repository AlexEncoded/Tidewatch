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
    indexes = {index["name"] for index in inspector.get_indexes("atmospheric_pressure_readings")}
    if "ix_atmospheric_pressure_readings_device_id" not in indexes:
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
