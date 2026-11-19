"""Store three-axis GNSS velocity samples for wave analysis."""

from alembic import op
import sqlalchemy as sa


revision = "0070_gnss_velocity"
down_revision = "0069_telemetry_job_fingerprint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "buoy_location_readings",
        sa.Column("velocity_east_mps", sa.Float(), nullable=True),
    )
    op.add_column(
        "buoy_location_readings",
        sa.Column("velocity_north_mps", sa.Float(), nullable=True),
    )
    op.add_column(
        "buoy_location_readings",
        sa.Column("velocity_up_mps", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("buoy_location_readings", "velocity_up_mps")
    op.drop_column("buoy_location_readings", "velocity_north_mps")
    op.drop_column("buoy_location_readings", "velocity_east_mps")
