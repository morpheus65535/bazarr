"""empty message

Revision ID: 30f37e2e15e1
Revises: cee6a710cb71
Create Date: 2023-12-26 21:32:39.283484

"""
from alembic import op
import sqlalchemy as sa
from app.database import TableShows


# revision identifiers, used by Alembic.
revision = '30f37e2e15e1'
down_revision = 'cee6a710cb71'
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
    if not column_exists('table_shows', 'monitored'):
        with op.batch_alter_table('table_shows', schema=None) as batch_op:
            batch_op.add_column(sa.Column('monitored', sa.Text(), nullable=True))
        op.execute(sa.update(TableShows).values({TableShows.monitored: 'True'}))


def downgrade():
    pass
