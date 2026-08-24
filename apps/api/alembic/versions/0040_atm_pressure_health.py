"""Add atmospheric pressure delta to sensor health checks."""

from alembic import op
import sqlalchemy as sa

revision = "0040_atm_pressure_health"
down_revision = "0039_atmospheric_pressure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("atmospheric_pressure_delta_kpa", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "atmospheric_pressure_delta_kpa")
