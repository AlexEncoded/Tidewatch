"""Add air temperature delta to sensor health checks."""

from alembic import op
import sqlalchemy as sa

revision = "0038_air_temp_health"
down_revision = "0037_air_temperature"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("air_temperature_delta_celsius", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "air_temperature_delta_celsius")
