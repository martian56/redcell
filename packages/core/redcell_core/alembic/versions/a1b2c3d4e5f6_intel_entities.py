"""intel entities and relations for OSINT

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "intel_entities",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("label", sa.String(), nullable=False, server_default=""),
        sa.Column("source", sa.String(), nullable=False, server_default=""),
        sa.Column("meta", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.UniqueConstraint("session_id", "type", "value", name="uq_intel_entity"),
    )
    op.create_index("ix_intel_entities_session_id", "intel_entities", ["session_id"])
    op.create_table(
        "intel_relations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("from_id", sa.String(), nullable=False),
        sa.Column("to_id", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False, server_default="related"),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.UniqueConstraint("from_id", "to_id", "label", name="uq_intel_relation"),
    )
    op.create_index("ix_intel_relations_session_id", "intel_relations", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_intel_relations_session_id", table_name="intel_relations")
    op.drop_table("intel_relations")
    op.drop_index("ix_intel_entities_session_id", table_name="intel_entities")
    op.drop_table("intel_entities")
