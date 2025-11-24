"""add trip_dates and user_availability

Revision ID: 0006_add_trip_dates_availability
Revises: 0005_modify_members_and_trips
Create Date: 2025-11-24 01:30:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006_add_trip_dates_availability'
down_revision = '0005_modify_members_and_trips'
branch_labels = None
depends_on = None


def upgrade():
    # add date range fields to trips
    with op.batch_alter_table('trips') as batch_op:
        batch_op.add_column(sa.Column('date_start', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('date_end', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('allowed_weekdays', sa.ARRAY(sa.Integer()), nullable=True))

    # create trip_dates
    op.create_table(
        'trip_dates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('trip_id', sa.Integer(), sa.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.UniqueConstraint('trip_id', 'date', name='uq_trip_date')
    )

    # create user_availability
    op.create_table(
        'user_availability',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('trip_date_id', sa.Integer(), sa.ForeignKey('trip_dates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='unset'),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('trip_date_id', 'user_id', name='uq_tripdate_user')
    )


def downgrade():
    op.drop_table('user_availability')
    op.drop_table('trip_dates')
    with op.batch_alter_table('trips') as batch_op:
        batch_op.drop_column('allowed_weekdays')
        batch_op.drop_column('date_end')
        batch_op.drop_column('date_start')
