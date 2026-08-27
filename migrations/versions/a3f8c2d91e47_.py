"""Add autoTranslate column to table_languages_profiles

Revision ID: a3f8c2d91e47
Revises: 537e9b4d10e3
Create Date: 2026-08-24 10:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f8c2d91e47'
down_revision = '537e9b4d10e3'
branch_labels = None
depends_on = None


bind = op.get_context().bind
insp = sa.inspect(bind)


def column_exists(table_name, column_name):
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)


def upgrade():
    with op.batch_alter_table('table_languages_profiles', schema=None) as batch_op:
        if not column_exists('table_languages_profiles', 'autoTranslate'):
            batch_op.add_column(sa.Column('autoTranslate', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('table_languages_profiles', schema=None) as batch_op:
        if column_exists('table_languages_profiles', 'autoTranslate'):
            batch_op.drop_column('autoTranslate')
