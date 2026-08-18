"""Persist sensor fallback decisions.

Revision ID: 0014_health_fallback_decisions
Revises: 0013_sensor_health_history
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_health_fallback_decisions"
down_revision = "0013_sensor_health_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_health_checks",
        sa.Column("decisions", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.alter_column("sensor_health_checks", "decisions", server_default=None)


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "decisions")
