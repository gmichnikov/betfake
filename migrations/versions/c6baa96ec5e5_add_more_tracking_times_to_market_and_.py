"""Add more tracking times to market and bet

Revision ID: c6baa96ec5e5
Revises: 5d57aa171d21
Create Date: 2024-02-10 08:17:26.109057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6baa96ec5e5'
down_revision = '5d57aa171d21'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bet', schema=None) as batch_op:
        batch_op.add_column(sa.Column('added_to_balance_time', sa.DateTime(), nullable=True))

    with op.batch_alter_table('market', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_time', sa.DateTime(), nullable=False))
        batch_op.add_column(sa.Column('marked_unavailable_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status_updated_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('market', schema=None) as batch_op:
        batch_op.drop_column('status_updated_time')
        batch_op.drop_column('marked_unavailable_time')
        batch_op.drop_column('created_time')

    with op.batch_alter_table('bet', schema=None) as batch_op:
        batch_op.drop_column('added_to_balance_time')

    # ### end Alembic commands ###