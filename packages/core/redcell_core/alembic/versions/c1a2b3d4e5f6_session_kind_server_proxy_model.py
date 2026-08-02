"""session kind/source/proxy/provider/model columns

Adds per-session execution + scan configuration:
  - kind      : "network" (default) or "code" (source scan)
  - source    : repo URL or folder path for a code scan
  - proxy_id  : chosen egress proxy (null = direct)
  - provider  : default LLM provider for runs in this session
  - model     : default LLM model for runs in this session

server_id already exists from the initial schema.

Revision ID: c1a2b3d4e5f6
Revises: bfbe26b46a24
Create Date: 2026-07-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "bfbe26b46a24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("kind", sa.String(), nullable=False, server_default="network"))
    op.add_column("sessions", sa.Column("source", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("proxy_id", sa.String(), nullable=True))
    op.add_column("sessions", sa.Column("provider", sa.String(), nullable=True))
    op.add_column("sessions", sa.Column("model", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "model")
    op.drop_column("sessions", "provider")
    op.drop_column("sessions", "proxy_id")
    op.drop_column("sessions", "source")
    op.drop_column("sessions", "kind")
