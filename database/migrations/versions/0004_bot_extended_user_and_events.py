"""bot extended: user fields (phone, full_name, birth_date, position) and events table

Revision ID: 0004_bot_extended
Revises: 0003_user_soft_delete
Create Date: 2026-02-28

"""
import sqlalchemy as sa
from alembic import op

revision = "0004_bot_extended"
down_revision = "0003_user_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("position", sa.String(length=255), nullable=True))

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("user_type", sa.Enum("horeca", "retail", "all", name="event_user_type"), nullable=False),
        sa.Column("event_date", sa.DateTime(), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("events")
    op.drop_column("users", "position")
    op.drop_column("users", "birth_date")
    op.drop_column("users", "full_name")
    op.drop_column("users", "phone_number")
