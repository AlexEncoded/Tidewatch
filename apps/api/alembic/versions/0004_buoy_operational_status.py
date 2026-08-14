"""Add operational status and last communication to buoys.

Revision ID: 0004_buoy_operational_status
Revises: 0003_buoy_location
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_buoy_operational_status"
down_revision: Union[str, Sequence[str], None] = "0003_buoy_location"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "buoys",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
    )
    op.add_column("buoys", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("buoys", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("buoys", "last_seen_at")
    op.drop_column("buoys", "status")
