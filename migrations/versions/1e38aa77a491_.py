"""empty message

Revision ID: 1e38aa77a491
Revises: 452dd0f0b578
Create Date: 2024-07-04 22:40:35.056744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e38aa77a491'
down_revision = '452dd0f0b578'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('table_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upgradedFromId', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(constraint_name='fk_history_upgradedFromId_id',
                                    referent_table='table_history',
                                    local_cols=['upgradedFromId'],
                                    remote_cols=['id'])

    with op.batch_alter_table('table_history_movie', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upgradedFromId', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(constraint_name='fk_history_movie_upgradedFromId_id',
                                    referent_table='table_history_movie',
                                    local_cols=['upgradedFromId'],
                                    remote_cols=['id'])

    with op.batch_alter_table('table_languages_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tag', sa.Text(), nullable=True))


def downgrade():
    pass
