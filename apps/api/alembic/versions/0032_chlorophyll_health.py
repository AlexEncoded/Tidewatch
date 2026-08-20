"""Add chlorophyll-a delta to sensor health checks.

Revision ID: 0032_chlorophyll_health
Revises: 0031_chlorophyll
"""

from alembic import op
import sqlalchemy as sa


revision = "0032_chlorophyll_health"
down_revision = "0031_chlorophyll"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("chlorophyll_a_delta_ug_l", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "chlorophyll_a_delta_ug_l")
