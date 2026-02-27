"""add admin email for dual login

Revision ID: 0002_admin_email_login
Revises: 0002_mailing_reliability
Create Date: 2026-02-27
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_admin_email_login"
down_revision = "0002_mailing_reliability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("admin_users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_column("admin_users", "email")

