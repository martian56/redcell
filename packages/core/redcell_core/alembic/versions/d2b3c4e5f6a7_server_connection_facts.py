"""server connection-test facts

Adds columns populated by the connection test (POST /servers/{id}/test):
os, latency_ms, last_check, last_error.

Revision ID: d2b3c4e5f6a7
Revises: c1a2b3d4e5f6
Create Date: 2026-07-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2b3c4e5f6a7"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("os", sa.String(), nullable=True))
    op.add_column("servers", sa.Column("latency_ms", sa.Integer(), nullable=True))
    op.add_column("servers", sa.Column("last_check", sa.String(), nullable=True))
    op.add_column("servers", sa.Column("last_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("servers", "last_error")
    op.drop_column("servers", "last_check")
    op.drop_column("servers", "latency_ms")
    op.drop_column("servers", "os")
