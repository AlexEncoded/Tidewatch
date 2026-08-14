"""Add optional geographic coordinates to buoys.

Revision ID: 0003_buoy_location
Revises: 0002_temperature_alerts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_buoy_location"
down_revision: Union[str, Sequence[str], None] = "0002_temperature_alerts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("buoys", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("buoys", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("buoys", "longitude")
    op.drop_column("buoys", "latitude")
