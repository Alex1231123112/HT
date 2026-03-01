"""events: max_places, event_registrations; content_plan content_type event

Revision ID: 0006_events_reg
Revises: 0005_content_plan
Create Date: 2026-02-28

"""
import sqlalchemy as sa
from alembic import op

revision = "0006_events_reg"
down_revision = "0005_content_plan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("max_places", sa.Integer(), nullable=True))

    op.create_table(
        "event_registrations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_registration_event_user"),
    )

    # Добавить значение 'event' в enum content_plan_content_type
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("ALTER TYPE content_plan_content_type ADD VALUE IF NOT EXISTS 'event'")
    # SQLite: enum хранится как строка, новых ограничений не добавляем — приложение может писать 'event'


def downgrade() -> None:
    op.drop_table("event_registrations")
    op.drop_column("events", "max_places")
    # Удалить 'event' из enum в PostgreSQL не обязательно для отката
