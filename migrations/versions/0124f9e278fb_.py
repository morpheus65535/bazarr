"""empty message

Revision ID: 0124f9e278fb
Revises: c00d40af333c
Create Date: 2025-12-21 21:54:24.686059

"""
from alembic import op
import sqlalchemy as sa
import ast

from app.database import TableEpisodesSubtitles, TableMoviesSubtitles


# revision identifiers, used by Alembic.
revision = '0124f9e278fb'
down_revision = '7e9a2b1c4d5f'
branch_labels = None
depends_on = None

bind = op.get_context().bind


def parse_language(language):
    split_language = language.split(':')
    return (
        split_language[0],
        bool(split_language[1] == 'hi') if len(split_language) > 1 else False,
        bool(split_language[1] == 'forced') if len(split_language) > 1 else False
    )


def upgrade():
    if bind.engine.name == 'postgresql':
        episodes_subtitles_column_exists = bind.exec_driver_sql('SELECT count(*) '
                                                                'FROM information_schema.columns '
                                                                'WHERE table_schema = \'public\' '
                                                                'AND table_name=\'table_episodes\' '
                                                                'AND column_name=\'subtitles\';')
    else:
        episodes_subtitles_column_exists = bind.exec_driver_sql('SELECT count(*) '
                                                                'FROM pragma_table_info(\'table_episodes\') '
                                                                'WHERE name=\'subtitles\';')
    episodes_subtitles_column_exists = bool(episodes_subtitles_column_exists.scalar())

    if episodes_subtitles_column_exists:
        # we do a raw SQL query to avoid the need to modify the TableEpisodes model
        try:
            episodes = bind.exec_driver_sql('SELECT "sonarrEpisodeId", "sonarrSeriesId", "subtitles" '
                                            'FROM table_episodes '
                                            'WHERE table_episodes.subtitles IS NOT NULL '
                                            'AND table_episodes.subtitles != \'[]\';')
        except sa.exc.OperationalError:
            pass
        else:
            for episode in episodes:
                try:
                    subtitles = ast.literal_eval(episode.subtitles)
                except Exception:
                    continue
                else:
                    for subtitle in subtitles:
                        subtitle_language = parse_language(subtitle[0])
                        try:
                            with bind.begin_nested():
                                bind.execute(sa.insert(TableEpisodesSubtitles).values(
                                    sonarrEpisodeId=episode.sonarrEpisodeId,
                                    sonarrSeriesId=episode.sonarrSeriesId,
                                    language=subtitle_language[0],
                                    hi=subtitle_language[1],
                                    forced=subtitle_language[2],
                                    path=subtitle[1],
                                    size=subtitle[2] if len(subtitle) > 2 else None
                                ))
                        except sa.exc.IntegrityError:
                            continue

            try:
                op.drop_column(column_name='subtitles', table_name='table_episodes')
            except sa.exc.OperationalError:
                bind.exec_driver_sql('UPDATE table_episodes SET subtitles = NULL;')

    if bind.engine.name == 'postgresql':
        movies_subtitles_column_exists = bind.exec_driver_sql('SELECT count(*) '
                                                              'FROM information_schema.columns '
                                                              'WHERE table_schema = \'public\' '
                                                              'AND table_name=\'table_movies\' '
                                                              'AND column_name=\'subtitles\';')
    else:
        movies_subtitles_column_exists = bind.exec_driver_sql('SELECT count(*) '
                                                              'FROM pragma_table_info(\'table_movies\') '
                                                              'WHERE name=\'subtitles\';')
    movies_subtitles_column_exists = bool(movies_subtitles_column_exists.scalar())

    if movies_subtitles_column_exists:
        # we do a raw SQL query to avoid the need to modify the TableMovies model
        try:
            movies = bind.exec_driver_sql('SELECT "radarrId", "subtitles" '
                                          'FROM table_movies '
                                          'WHERE table_movies.subtitles IS NOT NULL '
                                          'AND table_movies.subtitles != \'[]\';')
        except sa.exc.OperationalError:
            pass
        else:
            for movie in movies:
                try:
                    subtitles = ast.literal_eval(movie.subtitles)
                except Exception:
                    continue
                else:
                    for subtitle in subtitles:
                        subtitle_language = parse_language(subtitle[0])
                        try:
                            with bind.begin_nested():
                                bind.execute(sa.insert(TableMoviesSubtitles).values(
                                    radarrId=movie.radarrId,
                                    language=subtitle_language[0],
                                    hi=subtitle_language[1],
                                    forced=subtitle_language[2],
                                    path=subtitle[1],
                                    size=subtitle[2] if len(subtitle) > 2 else None
                                ))
                        except sa.exc.IntegrityError:
                            continue

            try:
                op.drop_column(column_name='subtitles', table_name='table_movies')
            except sa.exc.OperationalError:
                bind.exec_driver_sql('UPDATE table_movies SET subtitles = NULL;')

    """
    Create indexes for improved query performance based on analysis of:
    - Frequently used WHERE conditions
    - JOIN operations
    - ORDER BY clauses
    - Columns used in filtering and exclusion
    """

    # =========================================================================
    # EPISODES TABLE INDEXES
    # =========================================================================

    with op.batch_alter_table('table_episodes', schema=None) as batch_op:
        # Critical for "wanted" subtitle queries
        batch_op.create_index(
            'ix_episodes_missing_subtitles',
            ['missing_subtitles'],
            unique=False
        )

        # Most common JOIN column for episodes
        batch_op.create_index(
            'ix_episodes_series_id',
            ['sonarrSeriesId'],
            unique=False
        )

        # Composite index for exclusion clauses (monitored + series filtering)
        batch_op.create_index(
            'ix_episodes_monitored_series',
            ['monitored', 'sonarrSeriesId'],
            unique=False
        )

        # Used for ordering and display (season/episode number)
        batch_op.create_index(
            'ix_episodes_season_episode',
            ['season', 'episode'],
            unique=False
        )

        # Used for webhook lookups and file-based queries
        batch_op.create_index(
            'ix_episodes_episode_file_id',
            ['episode_file_id'],
            unique=False
        )

        # Used for subtitle refinement lookups
        batch_op.create_index(
            'ix_episodes_path',
            ['path'],
            unique=False
        )

    # =========================================================================
    # SHOWS TABLE INDEXES
    # =========================================================================

    with op.batch_alter_table('table_shows', schema=None) as batch_op:
        # Primary sorting column for series lists
        batch_op.create_index(
            'ix_shows_sort_title',
            ['sortTitle'],
            unique=False
        )

        # Used in exclusion clauses for monitored filtering
        batch_op.create_index(
            'ix_shows_monitored',
            ['monitored'],
            unique=False
        )

        # Used in exclusion clauses (tag-based filtering)
        batch_op.create_index(
            'ix_shows_tags',
            ['tags'],
            unique=False
        )

        # Foreign key for profile lookups
        batch_op.create_index(
            'ix_shows_profile_id',
            ['profileId'],
            unique=False
        )

        # Used in exclusion clauses
        batch_op.create_index(
            'ix_shows_series_type',
            ['seriesType'],
            unique=False
        )

    # =========================================================================
    # MOVIES TABLE INDEXES
    # =========================================================================

    with op.batch_alter_table('table_movies', schema=None) as batch_op:
        # Critical for "wanted" movie subtitle queries
        batch_op.create_index(
            'ix_movies_missing_subtitles',
            ['missing_subtitles'],
            unique=False
        )

        # Primary sorting column for movie lists
        batch_op.create_index(
            'ix_movies_sort_title',
            ['sortTitle'],
            unique=False
        )

        # Used in exclusion clauses for monitored filtering
        batch_op.create_index(
            'ix_movies_monitored',
            ['monitored'],
            unique=False
        )

        # Used in exclusion clauses (tag-based filtering)
        batch_op.create_index(
            'ix_movies_tags',
            ['tags'],
            unique=False
        )

        # Foreign key for profile lookups
        batch_op.create_index(
            'ix_movies_profile_id',
            ['profileId'],
            unique=False
        )

    # =========================================================================
    # HISTORY TABLE INDEXES (Episodes)
    # =========================================================================

    with op.batch_alter_table('table_history', schema=None) as batch_op:
        # Essential for DESC ordered history listings
        batch_op.create_index(
            'ix_history_timestamp',
            ['timestamp'],
            unique=False
        )

        # Foreign key used frequently in joins
        batch_op.create_index(
            'ix_history_episode_id',
            ['sonarrEpisodeId'],
            unique=False
        )

        # Foreign key used in joins
        batch_op.create_index(
            'ix_history_series_id',
            ['sonarrSeriesId'],
            unique=False
        )

        # Critical composite index for upgrade queries (GROUP BY both columns)
        batch_op.create_index(
            'ix_history_video_path_language',
            ['video_path', 'language'],
            unique=False
        )

        # Composite for upgrade logic (WHERE action IN + timestamp comparison)
        batch_op.create_index(
            'ix_history_action_timestamp',
            ['action', 'timestamp'],
            unique=False
        )

        # Used in upgrade tracking
        batch_op.create_index(
            'ix_history_upgraded_from_id',
            ['upgradedFromId'],
            unique=False
        )

        # Used in blacklist joins
        batch_op.create_index(
            'ix_history_subs_id',
            ['subs_id'],
            unique=False
        )

    # =========================================================================
    # HISTORY_MOVIE TABLE INDEXES
    # =========================================================================

    with op.batch_alter_table('table_history_movie', schema=None) as batch_op:
        # Essential for DESC ordered movie history listings
        batch_op.create_index(
            'ix_history_movie_timestamp',
            ['timestamp'],
            unique=False
        )

        # Foreign key used frequently in joins
        batch_op.create_index(
            'ix_history_movie_radarr_id',
            ['radarrId'],
            unique=False
        )

        # Critical composite index for movie upgrade queries
        batch_op.create_index(
            'ix_history_movie_video_path_language',
            ['video_path', 'language'],
            unique=False
        )

        # Composite for movie upgrade logic
        batch_op.create_index(
            'ix_history_movie_action_timestamp',
            ['action', 'timestamp'],
            unique=False
        )

        # Used in movie upgrade tracking
        batch_op.create_index(
            'ix_history_movie_upgraded_from_id',
            ['upgradedFromId'],
            unique=False
        )

        # Used in movie blacklist joins
        batch_op.create_index(
            'ix_history_movie_subs_id',
            ['subs_id'],
            unique=False
        )

    # =========================================================================
    # BLACKLIST TABLE INDEXES (Episodes)
    # =========================================================================

    with op.batch_alter_table('table_blacklist', schema=None) as batch_op:
        # Foreign key with ON DELETE CASCADE
        batch_op.create_index(
            'ix_blacklist_episode_id',
            ['sonarr_episode_id'],
            unique=False
        )

        # Foreign key with ON DELETE CASCADE
        batch_op.create_index(
            'ix_blacklist_series_id',
            ['sonarr_series_id'],
            unique=False
        )

        # Critical composite for blacklist lookups (provider + subs_id together)
        batch_op.create_index(
            'ix_blacklist_provider_subs_id',
            ['provider', 'subs_id'],
            unique=False
        )

        # Used for ordering blacklist listings
        batch_op.create_index(
            'ix_blacklist_timestamp',
            ['timestamp'],
            unique=False
        )

    # =========================================================================
    # BLACKLIST_MOVIE TABLE INDEXES
    # =========================================================================

    with op.batch_alter_table('table_blacklist_movie', schema=None) as batch_op:
        # Foreign key with ON DELETE CASCADE
        batch_op.create_index(
            'ix_blacklist_movie_radarr_id',
            ['radarr_id'],
            unique=False
        )

        # Critical composite for movie blacklist lookups
        batch_op.create_index(
            'ix_blacklist_movie_provider_subs_id',
            ['provider', 'subs_id'],
            unique=False
        )

        # Used for ordering movie blacklist listings
        batch_op.create_index(
            'ix_blacklist_movie_timestamp',
            ['timestamp'],
            unique=False
        )

    # =========================================================================
    # EPISODES SUBTITLES TABLE INDEXES
    # =========================================================================

    # TableEpisodesSubtitles indexes
    with op.batch_alter_table('table_episodes_subtitles', schema=None) as batch_op:
        batch_op.create_index(
            'idx_episodes_subtitles_sonarr_episode_id',
            ['sonarrEpisodeId'],
            unique=False
        )

        batch_op.create_index(
            'idx_episodes_subtitles_sonarr_series_id',
            ['sonarrSeriesId'],
            unique=False
        )

        batch_op.create_index(
            'idx_episodes_subtitles_path',
            ['path'],
            unique=False
        )

        batch_op.create_index(
            'idx_episodes_subtitles_embedded_track_id',
            ['embedded_track_id'],
            unique=False
        )

        batch_op.create_index(
            'idx_episodes_subtitles_composite',
            ['sonarrEpisodeId', 'path', 'embedded_track_id'],
            unique=False
        )

    # =========================================================================
    # MOVIES SUBTITLES TABLE INDEXES
    # =========================================================================

    # TableMoviesSubtitles indexes
    with op.batch_alter_table('table_movies_subtitles', schema=None) as batch_op:
        batch_op.create_index(
            'idx_movies_subtitles_radarr_id',
            ['radarrId'],
            unique=False
        )

        batch_op.create_index(
            'idx_movies_subtitles_path',
            ['path'],
            unique=False
        )

        batch_op.create_index(
            'idx_movies_subtitles_embedded_track_id',
            ['embedded_track_id'],
            unique=False
        )

        batch_op.create_index(
            'idx_movies_subtitles_composite',
            ['radarrId', 'path', 'embedded_track_id'],
            unique=False
        )


def downgrade():
    pass
