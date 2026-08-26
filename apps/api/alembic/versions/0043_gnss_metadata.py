"""Add optional GNSS metadata to buoy locations."""

from alembic import op
import sqlalchemy as sa

revision = "0043_gnss_metadata"
down_revision = "0042_acoustic_altimeter_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("buoy_location_readings", sa.Column("altitude_meters", sa.Float(), nullable=True))
    op.add_column("buoy_location_readings", sa.Column("speed_mps", sa.Float(), nullable=True))
    op.add_column("buoy_location_readings", sa.Column("hdop", sa.Float(), nullable=True))
    op.add_column("buoy_location_readings", sa.Column("satellites", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("buoy_location_readings", "satellites")
    op.drop_column("buoy_location_readings", "hdop")
    op.drop_column("buoy_location_readings", "speed_mps")
    op.drop_column("buoy_location_readings", "altitude_meters")
