"""Replace missing subtitle text columns with calculation state.

Revision ID: 9c2f6a8d4b10
Revises: f1d8a9c2b347
"""

from alembic import op
import sqlalchemy as sa
from typing import cast

revision = '9c2f6a8d4b10'
down_revision = 'f1d8a9c2b347'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for table_name in ('table_episodes', 'table_movies'):
        columns = {column['name'] for column in sa.inspect(bind).get_columns(table_name)}
        if 'missing_subtitles_calculated' not in columns:
            op.add_column(table_name, sa.Column(
                'missing_subtitles_calculated', sa.Boolean(), nullable=False, server_default=sa.false(),
            ))
        if 'missing_subtitles' in columns:
            media = sa.table(table_name, sa.column('missing_subtitles', sa.Text()),
                             sa.column('missing_subtitles_calculated', sa.Boolean()))
            bind.execute(media.update().values(
                missing_subtitles_calculated=media.c.missing_subtitles.is_not(None),
            ))
            with op.batch_alter_table(table_name) as batch_op:
                for index in sa.inspect(bind).get_indexes(table_name):
                    if 'missing_subtitles' in (index['column_names'] or []):
                        # SQLite and PostgreSQL give every reflected index a name.
                        batch_op.drop_index(cast(str, index['name']))
                batch_op.drop_column('missing_subtitles')
