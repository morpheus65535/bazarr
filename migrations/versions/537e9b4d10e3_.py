"""empty message

Revision ID: 537e9b4d10e3
Revises: 0124f9e278fb
Create Date: 2026-08-14 22:23:13.225829

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '537e9b4d10e3'
down_revision = '0124f9e278fb'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create indexes for table_episodes_subtitles and table_movies_subtitles
    to improve query performance on foreign key lookups and composite queries.
    """

    # =========================================================================
    # EPISODES SUBTITLES TABLE INDEXES
    # =========================================================================
    # Based on:
    # - Foreign key columns used in JOIN operations
    # - Filtering by path and embedded_track_id
    # - Composite lookups combining multiple columns

    with op.batch_alter_table('table_episodes_subtitles', schema=None) as batch_op:
        # Index for episode lookups (foreign key)
        batch_op.create_index(
            'ix_episodes_subtitles_sonarr_episode_id',
            ['sonarrEpisodeId'],
            unique=False
        )

        # Index for series lookups (foreign key)
        batch_op.create_index(
            'ix_episodes_subtitles_sonarr_series_id',
            ['sonarrSeriesId'],
            unique=False
        )

        # Index for path-based lookups (subtitle file path queries)
        batch_op.create_index(
            'ix_episodes_subtitles_path',
            ['path'],
            unique=False
        )

        # Index for embedded track lookups
        batch_op.create_index(
            'ix_episodes_subtitles_embedded_track_id',
            ['embedded_track_id'],
            unique=False
        )

        # Composite index for language and format filtering
        batch_op.create_index(
            'ix_episodes_subtitles_language_hi_forced',
            ['language', 'hi', 'forced'],
            unique=False
        )

        # Composite index combining episode ID, path, and track ID for complex lookups
        batch_op.create_index(
            'ix_episodes_subtitles_episode_path_track',
            ['sonarrEpisodeId', 'path', 'embedded_track_id'],
            unique=False
        )

    # =========================================================================
    # MOVIES SUBTITLES TABLE INDEXES
    # =========================================================================
    # Based on:
    # - Foreign key columns used in JOIN operations
    # - Filtering by path and embedded_track_id
    # - Composite lookups combining multiple columns

    with op.batch_alter_table('table_movies_subtitles', schema=None) as batch_op:
        # Index for movie lookups (foreign key)
        batch_op.create_index(
            'ix_movies_subtitles_radarr_id',
            ['radarrId'],
            unique=False
        )

        # Index for path-based lookups (subtitle file path queries)
        batch_op.create_index(
            'ix_movies_subtitles_path',
            ['path'],
            unique=False
        )

        # Index for embedded track lookups
        batch_op.create_index(
            'ix_movies_subtitles_embedded_track_id',
            ['embedded_track_id'],
            unique=False
        )

        # Composite index for language and format filtering
        batch_op.create_index(
            'ix_movies_subtitles_language_hi_forced',
            ['language', 'hi', 'forced'],
            unique=False
        )

        # Composite index combining movie ID, path, and track ID for complex lookups
        batch_op.create_index(
            'ix_movies_subtitles_movie_path_track',
            ['radarrId', 'path', 'embedded_track_id'],
            unique=False
        )


def downgrade():
    pass
