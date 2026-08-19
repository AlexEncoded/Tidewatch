"""Store marine current deltas in sensor health history.

Revision ID: 0022_marine_current_health_delta
Revises: 0021_marine_current_readings
"""

from alembic import op
import sqlalchemy as sa


revision = "0022_marine_current_health_delta"
down_revision = "0021_marine_current_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("marine_current_speed_delta_mps", sa.Float(), nullable=True),
    )
    op.add_column(
        "sensor_health_checks",
        sa.Column("marine_current_direction_delta_degrees", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "marine_current_direction_delta_degrees")
    op.drop_column("sensor_health_checks", "marine_current_speed_delta_mps")
