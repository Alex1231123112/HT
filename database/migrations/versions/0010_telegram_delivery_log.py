"""telegram_delivery_log: журнал отправок в Telegram

Revision ID: 0010_telegram_delivery_log
Revises: 0009_content_plan_items
Create Date: 2026-02-27

"""
import sqlalchemy as sa
from alembic import op

revision = "0010_telegram_delivery_log"
down_revision = "0009_content_plan_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telegram_delivery_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("content_plan.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_title", sa.String(length=255), nullable=False),
        sa.Column("channel_type", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("telegram_delivery_log")
