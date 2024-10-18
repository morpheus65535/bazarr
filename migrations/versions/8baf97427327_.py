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


def upgrade():
    with op.batch_alter_table('table_episodes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at_timestamp', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True))

    with op.batch_alter_table('table_movies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at_timestamp', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True))

    with op.batch_alter_table('table_shows', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at_timestamp', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at_timestamp', sa.DateTime(), nullable=True))


def downgrade():
    pass
