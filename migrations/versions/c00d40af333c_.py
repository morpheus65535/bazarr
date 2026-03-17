"""empty message

Revision ID: c00d40af333c
Revises: df76a4410347
Create Date: 2026-03-15 10:22:57.387298

"""
from alembic import op
import sqlalchemy as sa
from app.database import TableHistory, TableHistoryMovie


# revision identifiers, used by Alembic.
revision = 'c00d40af333c'
down_revision = 'df76a4410347'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    with op.batch_alter_table('table_history', schema=None) as batch_op:
        if not column_exists('table_history', 'score_out_of'):
            batch_op.add_column(sa.Column('score_out_of', sa.Integer, nullable=True))
    op.execute(sa.update(TableHistory).values({TableHistory.score_out_of: 360}).where(TableHistory.score.is_not(None)))

    with op.batch_alter_table('table_history_movie', schema=None) as batch_op:
        if not column_exists('table_history_movie', 'score_out_of'):
            batch_op.add_column(sa.Column('score_out_of', sa.Integer, nullable=True))
    op.execute(sa.update(TableHistoryMovie).values({TableHistoryMovie.score_out_of: 120}).where(TableHistoryMovie.score.is_not(None)))


def downgrade():
    pass
