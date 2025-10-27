
"""create trips table

Revision ID: 0002_create_trips
Revises: 0001_create_users
Create Date: 2025-10-27 22:00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_create_trips'
down_revision = '0001_create_users'
branch_labels = None
depends_on = None


def upgrade():
    # Create trips table. Removed start/end dates and created_at per request.
    # Added `hash_id` as a unique identifier used to connect to a trip.
    op.create_table(
        'trips',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('hash_id', sa.String(length=64), nullable=False, unique=True),
    )


def downgrade():
    op.drop_table('trips')
