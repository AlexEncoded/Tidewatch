"""Store turbidity delta in sensor health history.

Revision ID: 0024_turbidity_health_delta
Revises: 0023_turbidity_readings
"""

from alembic import op
import sqlalchemy as sa


revision = "0024_turbidity_health_delta"
down_revision = "0023_turbidity_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("turbidity_delta_ntu", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "turbidity_delta_ntu")
