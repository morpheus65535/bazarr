"""empty message

Revision ID: 8baf97427327
Revises: 1e38aa77a491
Create Date: 2024-10-18 12:57:13.831596

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8baf97427327'
down_revision = '1e38aa77a491'
branch_labels = None
depends_on = None


bind = op.get_context().bind
insp = sa.inspect(bind)
tables = insp.get_table_names()
sqlite = bind.engine.name == 'sqlite'


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    with op.batch_alter_table('table_episodes', schema=None) as batch_op:
        if not column_exists('table_episodes', 'created_at_timestamp'):
            batch_op.add_column(sa.Column('created_at_timestamp', sa.DateTime(), nullable=True))
        if not column_exists('table_episodes', 'updated_at_timestamp'):
            batch_op.add_column(sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True))

    with op.batch_alter_table('table_movies', schema=None) as batch_op:
        if not column_exists('table_movies', 'created_at_timestamp'):
            batch_op.add_column(sa.Column('created_at_timestamp', sa.DateTime(), nullable=True))
        if not column_exists('table_movies', 'updated_at_timestamp'):
            batch_op.add_column(sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True))

    with op.batch_alter_table('table_shows', schema=None) as batch_op:
        if not column_exists('table_shows', 'created_at_timestamp'):
            batch_op.add_column(sa.Column('created_at_timestamp', sa.DateTime(), nullable=True))
        if not column_exists('table_shows', 'updated_at_timestamp'):
            batch_op.add_column(sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True))


def downgrade():
    pass
