"""modify user_trips and trips

Revision ID: 0005_modify_members_and_trips
Revises: 0004_drop_user_name
Create Date: 2025-11-24 00:30:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005_modify_members_and_trips'
down_revision = '0004_drop_user_name'
branch_labels = None
depends_on = None


def upgrade():
    # Remove owner_id from trips
    with op.batch_alter_table('trips') as batch_op:
        batch_op.drop_column('owner_id')

    # Modify user_trips: drop is_owner, add user_name
    with op.batch_alter_table('user_trips') as batch_op:
        # Drop boolean column if present
        try:
            batch_op.drop_column('is_owner')
        except Exception:
            # Column may not exist in some states; ignore
            pass
        batch_op.add_column(sa.Column('user_name', sa.String(length=128), nullable=False))


def downgrade():
    # Re-add owner_id to trips (nullable)
    with op.batch_alter_table('trips') as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))

    # Revert user_trips changes: remove user_name, add is_owner
    with op.batch_alter_table('user_trips') as batch_op:
        batch_op.drop_column('user_name')
        batch_op.add_column(sa.Column('is_owner', sa.Boolean(), nullable=False, server_default=sa.text('false')))
