"""report artifacts + branding settings

Adds report generation columns (formats/artifacts/summary/error) and a report
branding blob on app_settings.

Revision ID: a5b6c7d8e9f0
Revises: f4d5e6a7b8c9
Create Date: 2026-07-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, None] = "f4d5e6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("formats", JSONB(), nullable=False, server_default="[]"))
    op.add_column("reports", sa.Column("artifacts", JSONB(), nullable=False, server_default="{}"))
    op.add_column("reports", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("reports", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("app_settings", sa.Column("report", JSONB(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("app_settings", "report")
    op.drop_column("reports", "error")
    op.drop_column("reports", "summary")
    op.drop_column("reports", "artifacts")
    op.drop_column("reports", "formats")
