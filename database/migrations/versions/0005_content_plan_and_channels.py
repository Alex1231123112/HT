"""content plan and distribution channels

Revision ID: 0005_content_plan
Revises: 0004_bot_extended
Create Date: 2026-02-28

"""
import sqlalchemy as sa
from alembic import op

revision = "0005_content_plan"
down_revision = "0004_bot_extended"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "distribution_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "channel_type",
            sa.Enum("bot", "telegram_channel", name="distribution_channel_type"),
            nullable=False,
        ),
        sa.Column("telegram_ref", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "content_plan",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "content_type",
            sa.Enum("promotion", "news", "delivery", "custom", name="content_plan_content_type"),
            nullable=False,
        ),
        sa.Column("content_id", sa.Integer(), nullable=True),
        sa.Column("custom_title", sa.String(length=255), nullable=True),
        sa.Column("custom_description", sa.Text(), nullable=True),
        sa.Column("custom_media_url", sa.String(length=500), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "scheduled", "sent", "cancelled", name="content_plan_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "content_plan_channels",
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("content_plan.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "channel_id",
            sa.Integer(),
            sa.ForeignKey("distribution_channels.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("content_plan_channels")
    op.drop_table("content_plan")
    op.drop_table("distribution_channels")
