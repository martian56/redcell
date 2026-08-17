"""session brief + run instruction

Adds a distilled engagement brief on sessions and a per-run instruction on runs,
both fed to the orchestrator as operator context.

Revision ID: b7c8d9e0f1a2
Revises: a5b6c7d8e9f0
Create Date: 2026-08-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("brief", sa.Text(), nullable=True))
    op.add_column("runs", sa.Column("instruction", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "instruction")
    op.drop_column("sessions", "brief")
