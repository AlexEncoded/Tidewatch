"""Add humidity delta to sensor health checks.

Revision ID: 0036_humidity_health
Revises: 0035_humidity
"""

from alembic import op
import sqlalchemy as sa

revision = "0036_humidity_health"
down_revision = "0035_humidity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("humidity_delta_percent", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "humidity_delta_percent")
