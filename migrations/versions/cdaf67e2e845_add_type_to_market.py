"""Add type to Market

Revision ID: cdaf67e2e845
Revises: 4bc3f29ab292
Create Date: 2024-02-10 07:35:45.919479

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cdaf67e2e845'
down_revision = '4bc3f29ab292'
branch_labels = None
depends_on = None

markettype_enum = sa.Enum('h2h', 'spreads', 'totals', name='markettype')

def upgrade():
    markettype_enum.create(op.get_bind(), checkfirst=True)

    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('market', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', markettype_enum, nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('market', schema=None) as batch_op:
        batch_op.drop_column('type')

    markettype_enum.drop(op.get_bind(), checkfirst=True)

    # ### end Alembic commands ###