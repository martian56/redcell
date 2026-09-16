"""session_servers join table for multi-server sessions

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "session_servers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("server_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="execution"),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.UniqueConstraint("session_id", "server_id", "role", name="uq_session_server_role"),
    )
    op.create_index("ix_session_servers_session_id", "session_servers", ["session_id"])
    op.execute(
        "INSERT INTO session_servers (id, session_id, server_id, role, created_at) "
        "SELECT 'ssv_' || id, id, server_id, 'execution', created_at "
        "FROM sessions WHERE server_id IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_session_servers_session_id", table_name="session_servers")
    op.drop_table("session_servers")
