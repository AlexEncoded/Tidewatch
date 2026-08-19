"""Add dissolved oxygen delta to sensor health checks.

Revision ID: 0026_dissolved_oxygen_health_delta
Revises: 0025_dissolved_oxygen_readings
"""

from alembic import op
import sqlalchemy as sa


revision = "0026_do_health_delta"
down_revision = "0025_dissolved_oxygen_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("dissolved_oxygen_delta_mg_l", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "dissolved_oxygen_delta_mg_l")
