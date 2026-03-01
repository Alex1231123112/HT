"""add soft delete field to users

Revision ID: 0003_user_soft_delete
Revises: 0002_admin_email_login
Create Date: 2026-02-26
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_user_soft_delete"
down_revision = "0002_admin_email_login"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")
