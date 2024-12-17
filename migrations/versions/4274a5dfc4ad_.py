"""empty message

Revision ID: 4274a5dfc4ad
Revises: 8baf97427327
Create Date: 2024-12-15 21:19:19.406290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4274a5dfc4ad'
down_revision = '8baf97427327'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    if not column_exists('table_shows', 'ended'):
        with op.batch_alter_table('table_shows', schema=None) as batch_op:
            batch_op.add_column(sa.Column('ended', sa.TEXT(), nullable=True))

    if not column_exists('table_shows', 'lastAired'):
        with op.batch_alter_table('table_shows', schema=None) as batch_op:
            batch_op.add_column(sa.Column('lastAired', sa.TEXT(), nullable=True))


def downgrade():
    pass
