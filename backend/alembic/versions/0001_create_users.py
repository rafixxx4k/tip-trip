"""create users table

Revision ID: 0001_create_users
Revises: None
Create Date: 2025-10-27 21:20:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_create_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False, unique=True),
        sa.Column('token', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('users')
