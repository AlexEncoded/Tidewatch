"""Track the last batch received from each physical device."""

from alembic import op
import sqlalchemy as sa


revision = "0047_device_last_seen"
down_revision = "0046_devices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "devices", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("devices", "last_seen_at")
