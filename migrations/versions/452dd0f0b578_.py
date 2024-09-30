"""empty message

Revision ID: 452dd0f0b578
Revises: b183a2ac0dd1
Create Date: 2024-05-06 20:27:15.618027

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '452dd0f0b578'
down_revision = 'b183a2ac0dd1'
branch_labels = None
depends_on = None

bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    if column_exists('table_shows', 'alternativeTitle'):
        with op.batch_alter_table('table_shows', schema=None) as batch_op:
            batch_op.drop_column('alternativeTitle')

    if not column_exists('table_languages_profiles', 'originalFormat'):
        with op.batch_alter_table('table_languages_profiles', schema=None) as batch_op:
            batch_op.add_column(sa.Column('originalFormat', sa.Integer(), server_default='0'))

    if not column_exists('table_languages_profiles', 'mustContain'):
        with op.batch_alter_table('table_languages_profiles', schema=None) as batch_op:
            batch_op.add_column(sa.Column('mustContain', sa.Text(), server_default='[]'))

    if not column_exists('table_languages_profiles', 'mustNotContain'):
        with op.batch_alter_table('table_languages_profiles', schema=None) as batch_op:
            batch_op.add_column(sa.Column('mustNotContain', sa.Text(), server_default='[]'))


def downgrade():
    pass
