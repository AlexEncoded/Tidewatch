"""Add rainfall delta to sensor health checks.

Revision ID: 0034_rain_health
Revises: 0033_rainfall
"""

from alembic import op
import sqlalchemy as sa


revision = "0034_rain_health"
down_revision = "0033_rainfall"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("rainfall_delta_mm_h", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "rainfall_delta_mm_h")
