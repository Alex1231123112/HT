"""mailing reliability fields

Revision ID: 0002_mailing_reliability
Revises: 0001_initial
Create Date: 2026-02-26
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_mailing_reliability"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mailings", sa.Column("send_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("mailings", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("mailings", sa.Column("cancelled_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("mailings", "cancelled_at")
    op.drop_column("mailings", "last_error")
    op.drop_column("mailings", "send_attempts")
