"""Store wind deltas in sensor health history.

Revision ID: 0020_wind_health_delta
Revises: 0019_wind_readings
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_wind_health_delta"
down_revision = "0019_wind_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("wind_speed_delta_mps", sa.Float(), nullable=True))
    op.add_column(
        "sensor_health_checks",
        sa.Column("wind_direction_delta_degrees", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "wind_direction_delta_degrees")
    op.drop_column("sensor_health_checks", "wind_speed_delta_mps")
