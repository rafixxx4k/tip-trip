"""add expenses tables

Revision ID: 0007_add_expenses
Revises: 0006_add_trip_dates_availability
Create Date: 2026-01-16 12:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007_add_expenses"
down_revision = "0006_add_trip_dates_availability"
branch_labels = None
depends_on = None


def upgrade():
    # create expenses table
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "trip_id",
            sa.Integer(),
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payer_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "currency", sa.String(length=10), nullable=False, server_default="USD"
        ),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_expenses_trip_id", "expenses", ["trip_id"])

    # create expense_shares table
    op.create_table(
        "expense_shares",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "expense_id",
            sa.Integer(),
            sa.ForeignKey("expenses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "share_type", sa.String(length=20), nullable=False, server_default="equal"
        ),
        sa.Column("value", sa.Float(), nullable=False),
    )
    op.create_index("ix_expense_shares_expense_id", "expense_shares", ["expense_id"])


def downgrade():
    op.drop_index("ix_expense_shares_expense_id", table_name="expense_shares")
    op.drop_table("expense_shares")
    op.drop_index("ix_expenses_trip_id", table_name="expenses")
    op.drop_table("expenses")
