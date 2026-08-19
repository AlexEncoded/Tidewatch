"""Add conductivity delta to sensor health checks.

Revision ID: 0030_conductivity_health
Revises: 0029_conductivity
"""

from alembic import op
import sqlalchemy as sa


revision = "0030_conductivity_health"
down_revision = "0029_conductivity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("conductivity_delta_us_cm", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "conductivity_delta_us_cm")
