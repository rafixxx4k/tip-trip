"""drop name column from users

Revision ID: 0004_drop_user_name
Revises: 0003_create_user_trips
Create Date: 2025-11-24 00:00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_drop_user_name'
down_revision = '0003_create_user_trips'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the unused `name` column from users
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('name')


def downgrade():
    # Re-add the `name` column if downgrading
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(), nullable=True))
