"""empty message

Revision ID: 195144da1f7e
Revises: 95cd4cf40d7a
Create Date: 2023-07-27 13:14:08.825037

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '195144da1f7e'
down_revision = '95cd4cf40d7a'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)
tables = insp.get_table_names()


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    with op.batch_alter_table('table_episodes') as batch_op:
        if column_exists('table_episodes', 'rowid'):
            batch_op.drop_column(column_name='rowid')

    with op.batch_alter_table('table_movies') as batch_op:
        if column_exists('table_movies', 'rowid'):
            batch_op.drop_column(column_name='rowid')

    if 'table_custom_score_profiles' in tables:
        op.drop_table('table_custom_score_profiles')

    if 'table_custom_score_profile_conditions' in tables:
        op.drop_table('table_custom_score_profile_conditions')


def downgrade():
    pass
