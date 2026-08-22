"""Add redundant air temperature readings."""

from alembic import op
import sqlalchemy as sa

revision = "0037_air_temperature"
down_revision = "0036_humidity_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "air_temperature_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("air_temperature_celsius", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_air_temperature_readings_buoy_id", "air_temperature_readings", ["buoy_id"])
    op.create_index("ix_air_temperature_readings_measured_at", "air_temperature_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_air_temperature_readings_measured_at", table_name="air_temperature_readings")
    op.drop_index("ix_air_temperature_readings_buoy_id", table_name="air_temperature_readings")
    op.drop_table("air_temperature_readings")
