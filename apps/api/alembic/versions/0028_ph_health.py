"""Add pH delta to sensor health checks.

Revision ID: 0028_ph_health
Revises: 0027_ph_readings
"""

from alembic import op
import sqlalchemy as sa


revision = "0028_ph_health"
down_revision = "0027_ph_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("ph_delta", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "ph_delta")
