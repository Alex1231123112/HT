"""content_plan_items: несколько сообщений в одном плане

Revision ID: 0009_content_plan_items
Revises: 0008_managers
Create Date: 2026-02-27

"""
import sqlalchemy as sa
from alembic import op

revision = "0009_content_plan_items"
down_revision = "0008_managers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        # Тип content_plan_content_type уже есть в БД (миграции 0005/0006) — не создаём заново
        op.execute(
            """
            CREATE TABLE content_plan_items (
                id SERIAL PRIMARY KEY,
                plan_id INTEGER NOT NULL REFERENCES content_plan(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                content_type content_plan_content_type NOT NULL,
                content_id INTEGER,
                custom_title VARCHAR(255),
                custom_description TEXT,
                custom_media_url VARCHAR(500)
            )
            """
        )
    else:
        op.create_table(
            "content_plan_items",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("plan_id", sa.Integer(), sa.ForeignKey("content_plan.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "content_type",
                sa.Enum("promotion", "news", "delivery", "event", "custom", name="content_plan_content_type"),
                nullable=False,
            ),
            sa.Column("content_id", sa.Integer(), nullable=True),
            sa.Column("custom_title", sa.String(length=255), nullable=True),
            sa.Column("custom_description", sa.Text(), nullable=True),
            sa.Column("custom_media_url", sa.String(length=500), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("content_plan_items")
