"""managers table (separate from users)

Revision ID: 0008_managers
Revises: 0007_establishments
Create Date: 2026-03-02

"""
import sqlalchemy as sa
from alembic import op

revision = "0008_managers"
down_revision = "0007_establishments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "managers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("telegram_username", sa.String(length=255), nullable=True),
        sa.Column("telegram_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("establishment", sa.String(length=500), nullable=False),
        sa.Column(
            "user_type",
            sa.Enum("horeca", "retail", "all", name="managers_user_type"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("managers")
    op.execute("DROP TYPE IF EXISTS managers_user_type")
