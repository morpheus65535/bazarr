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

bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    with op.batch_alter_table('table_history') as batch_op:
        if not column_exists('table_history', 'matched'):
            batch_op.add_column(sa.Column('matched', sa.Text))
        if not column_exists('table_history', 'not_matched'):
            batch_op.add_column(sa.Column('not_matched', sa.Text))

    with op.batch_alter_table('table_history_movie') as batch_op:
        if not column_exists('table_history_movie', 'matched'):
            batch_op.add_column(sa.Column('matched', sa.Text))
        if not column_exists('table_history_movie', 'not_matched'):
            batch_op.add_column(sa.Column('not_matched', sa.Text))


def downgrade():
    pass
