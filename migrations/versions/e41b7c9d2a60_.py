"""Repair databases that missed the series TMDB id and the lookup indexes.

A database built from the sportarr branch before it merged development was
stamped past ca7df64674ee and 3b8e5d1a7f20, so those two revisions never ran
on it. This revision adds what they create when it is missing, and does
nothing on a database that has it.

Revision ID: e41b7c9d2a60
Revises: d8b3f0c4e215
Create Date: 2026-11-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e41b7c9d2a60'
down_revision = 'd8b3f0c4e215'
branch_labels = None
depends_on = None

# The indexes that revision 3b8e5d1a7f20 creates, by table.
INDEXES = {
    'table_episodes': [('ix_episodes_tvdb_id', ['tvdbId'])],
    'table_shows': [('ix_shows_imdb_id', ['imdbId'])],
    'table_movies': [('ix_movies_imdb_id', ['imdbId']), ('ix_movies_movie_file_id', ['movie_file_id'])],
}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    # Revision ca7df64674ee
    columns = {column['name'] for column in inspector.get_columns('table_shows')}
    if 'tmdbId' not in columns:
        op.add_column('table_shows', sa.Column('tmdbId', sa.Integer(), nullable=True))

    # Revision 3b8e5d1a7f20
    for table, indexes in INDEXES.items():
        existing = {index['name'] for index in inspector.get_indexes(table)}
        for name, index_columns in indexes:
            if name not in existing:
                op.create_index(name, table, index_columns, unique=False)


def downgrade() -> None:
    pass
