"""empty message

Revision ID: 95cd4cf40d7a
Revises: dc09994b7e65
Create Date: 2023-05-30 08:44:11.636511

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95cd4cf40d7a'
down_revision = 'dc09994b7e65'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('table_history') as batch_op:
        batch_op.add_column(sa.Column('matched', sa.Text))
        batch_op.add_column(sa.Column('not_matched', sa.Text))

    with op.batch_alter_table('table_history_movie') as batch_op:
        batch_op.add_column(sa.Column('matched', sa.Text))
        batch_op.add_column(sa.Column('not_matched', sa.Text))


def downgrade():
    pass
