"""Store ambient light delta in sensor health history.

Revision ID: 0018_ambient_light_health_delta
Revises: 0017_ambient_light_readings
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_ambient_light_health_delta"
down_revision = "0017_ambient_light_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("ambient_light_delta_lux", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "ambient_light_delta_lux")
