"""initial

Revision ID: d9507454e5ee
Revises: 
Create Date: 2020-11-07 22:03:04.290006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9507454e5ee'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('telegram_id', sa.Integer(), nullable=True),
    sa.Column('first_name', sa.String(length=255), nullable=True),
    sa.Column('tipo_credentials', sa.String(length=1000), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    # ### end Alembic commands ###