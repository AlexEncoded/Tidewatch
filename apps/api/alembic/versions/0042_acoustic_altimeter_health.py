"""Add acoustic altimeter health delta."""

from alembic import op
import sqlalchemy as sa

revision = "0042_acoustic_altimeter_health"
down_revision = "0041_acoustic_altimeter"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("acoustic_altimeter_delta_meters", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "acoustic_altimeter_delta_meters")
