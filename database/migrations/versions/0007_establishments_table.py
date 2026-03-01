"""establishments table for CRUD

Revision ID: 0007_establishments
Revises: 0006_events_reg
Create Date: 2026-03-01

"""
import sqlalchemy as sa
from alembic import op

revision = "0007_establishments"
down_revision = "0006_events_reg"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "establishments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "user_type",
            sa.Enum("horeca", "retail", "all", name="establishment_user_type"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("establishments")
    op.execute("DROP TYPE IF EXISTS establishment_user_type")
