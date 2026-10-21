"""Add TMDB ID to series.

Revision ID: ca7df64674ee
Revises: a4c7e1f29b03
"""

from alembic import op
import sqlalchemy as sa

revision = 'ca7df64674ee'
down_revision = 'a4c7e1f29b03'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column['name'] for column in sa.inspect(bind).get_columns('table_shows')}
    if 'tmdbId' not in columns:
        op.add_column('table_shows', sa.Column('tmdbId', sa.Integer(), nullable=True))

    # Existing rows stay NULL until the next Sonarr sync writes their TMDB ID.


def downgrade() -> None:
    pass
