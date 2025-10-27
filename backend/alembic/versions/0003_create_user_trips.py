"""create user_trips association table

Revision ID: 0003_create_user_trips
Revises: 0002_create_trips
Create Date: 2025-10-27 22:30:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003_create_user_trips'
down_revision = '0002_create_trips'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_trips',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trip_id', sa.Integer(), sa.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_owner', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.UniqueConstraint('user_id', 'trip_id', name='uq_user_trip')
    )


def downgrade():
    op.drop_table('user_trips')
