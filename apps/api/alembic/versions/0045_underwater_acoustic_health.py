"""Add underwater acoustic health delta."""

from alembic import op
import sqlalchemy as sa


revision = "0045_underwater_acoustic_health"
down_revision = "0044_underwater_acoustic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sensor_health_checks", sa.Column("underwater_acoustic_delta_db", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensor_health_checks", "underwater_acoustic_delta_db")
