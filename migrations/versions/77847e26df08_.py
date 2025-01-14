"""empty message

Revision ID: 77847e26df08
Revises: d20f86346072
Create Date: 2022-08-16 15:09:03.834365

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77847e26df08'
down_revision = 'd20f86346072'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_venues', sa.Boolean(), nullable=True))
    op.drop_column('Artist', 'looking_for_venues')
    op.add_column('Venue', sa.Column('seeking_talent', sa.Boolean(), nullable=True))
    op.drop_column('Venue', 'looking_for_talent')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('looking_for_talent', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('Venue', 'seeking_talent')
    op.add_column('Artist', sa.Column('looking_for_venues', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('Artist', 'seeking_venues')
    # ### end Alembic commands ###
