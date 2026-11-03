"""Add indexes for movie file ffprobe lookups and Plex webhook lookups.

Indexes table_movies.movie_file_id (ffprobe cache lookups), table_episodes.tvdbId,
table_shows.imdbId and table_movies.imdbId (Plex webhook lookups).

Revision ID: 3b8e5d1a7f20
Revises: ca7df64674ee
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '3b8e5d1a7f20'
down_revision = 'ca7df64674ee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('table_episodes', schema=None) as batch_op:
        # TVDB ID lookup used by the Plex webhook to resolve the series
        batch_op.create_index(
            'ix_episodes_tvdb_id',
            ['tvdbId'],
            unique=False
        )

    with op.batch_alter_table('table_shows', schema=None) as batch_op:
        # IMDb ID lookup used by the Plex webhook to resolve the series
        batch_op.create_index(
            'ix_shows_imdb_id',
            ['imdbId'],
            unique=False
        )

    with op.batch_alter_table('table_movies', schema=None) as batch_op:
        # IMDb ID lookup used by the Plex webhook to resolve the movie
        batch_op.create_index(
            'ix_movies_imdb_id',
            ['imdbId'],
            unique=False
        )

        # Used for webhook lookups and file-based queries
        batch_op.create_index(
            'ix_movies_movie_file_id',
            ['movie_file_id'],
            unique=False
        )


def downgrade() -> None:
    pass
