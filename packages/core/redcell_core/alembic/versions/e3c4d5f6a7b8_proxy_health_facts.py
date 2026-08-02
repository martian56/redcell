"""proxy health-check facts

Adds columns populated by the proxy health test (POST /proxies/{id}/test):
last_error, egress_ip.

Revision ID: e3c4d5f6a7b8
Revises: d2b3c4e5f6a7
Create Date: 2026-07-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3c4d5f6a7b8"
down_revision: Union[str, None] = "d2b3c4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("proxies", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("proxies", sa.Column("egress_ip", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("proxies", "egress_ip")
    op.drop_column("proxies", "last_error")
