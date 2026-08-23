"""Add redundant atmospheric pressure readings."""

from alembic import op
import sqlalchemy as sa

revision = "0039_atmospheric_pressure"
down_revision = "0038_air_temp_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "atmospheric_pressure_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("buoy_id", sa.String(length=32), nullable=False),
        sa.Column("atmospheric_pressure_kpa", sa.Float(), nullable=False),
        sa.Column("sensor_channel", sa.String(length=1), nullable=False),
        sa.Column("sensor_id", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column("quality", sa.String(length=12), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["buoy_id"], ["buoys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_atmospheric_pressure_readings_buoy_id", "atmospheric_pressure_readings", ["buoy_id"])
    op.create_index("ix_atmospheric_pressure_readings_measured_at", "atmospheric_pressure_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("ix_atmospheric_pressure_readings_measured_at", table_name="atmospheric_pressure_readings")
    op.drop_index("ix_atmospheric_pressure_readings_buoy_id", table_name="atmospheric_pressure_readings")
    op.drop_table("atmospheric_pressure_readings")
