"""empty message

Revision ID: 309dc062d2e4
Revises: c00d40af333c
Create Date: 2026-03-30 21:47:35.596074

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '309dc062d2e4'
down_revision = 'c00d40af333c'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    if not column_exists('table_episodes', 'tvdbId'):
        with op.batch_alter_table('table_episodes', schema=None) as batch_op:
            batch_op.add_column(sa.Column('tvdbId', sa.Integer(), nullable=True))


def downgrade():
    pass
