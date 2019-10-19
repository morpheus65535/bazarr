import os
import atexit

from get_args import args
from peewee import *
from playhouse.migrate import *

from helper import path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie

database = SqliteDatabase(os.path.join(args.config_dir, 'db', 'bazarr.db'))
database.pragma('wal_checkpoint', 'TRUNCATE')  # Run a checkpoint and merge remaining wal-journal.
database.timeout = 30  # Number of second to wait for database
database.cache_size = -1024  # Number of KB of cache for wal-journal.
                             # Must be negative because positive means number of pages.
database.wal_autocheckpoint = 50  # Run an automatic checkpoint every 50 write transactions.


@database.func('path_substitution')
def path_substitution(path):
    return path_replace(path)


@database.func('path_substitution_movie')
def path_substitution_movie(path):
    return path_replace_movie(path)


class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database


class System(BaseModel):
    configured = TextField(null=True)
    updated = TextField(null=True)

    class Meta:
        table_name = 'system'
        primary_key = False


class TableShows(BaseModel):
    alternate_titles = TextField(column_name='alternateTitles', null=True)
    audio_language = TextField(null=True)
    fanart = TextField(null=True)
    forced = TextField(null=True, constraints=[SQL('DEFAULT "False"')])
    hearing_impaired = TextField(null=True)
    languages = TextField(null=True)
    overview = TextField(null=True)
    path = TextField(null=False, unique=True)
    poster = TextField(null=True)
    sonarr_series_id = IntegerField(column_name='sonarrSeriesId', null=True, unique=True)
    sort_title = TextField(column_name='sortTitle', null=True)
    title = TextField(null=True)
    tvdb_id = IntegerField(column_name='tvdbId', null=True, unique=True, primary_key=True)
    year = TextField(null=True)

    class Meta:
        table_name = 'table_shows'


class TableEpisodes(BaseModel):
    rowid = IntegerField()
    audio_codec = TextField(null=True)
    episode = IntegerField(null=False)
    failed_attempts = TextField(column_name='failedAttempts', null=True)
    format = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    path = TextField(null=False)
    resolution = TextField(null=True)
    scene_name = TextField(null=True)
    season = IntegerField(null=False)
    sonarr_episode_id = IntegerField(column_name='sonarrEpisodeId', unique=True, null=False)
    sonarr_series_id = ForeignKeyField(TableShows, field='sonarr_series_id', column_name='sonarrSeriesId', null=False)
    subtitles = TextField(null=True)
    title = TextField(null=True)
    video_codec = TextField(null=True)
    episode_file_id = IntegerField(null=True)

    class Meta:
        table_name = 'table_episodes'
        primary_key = False


class TableMovies(BaseModel):
    rowid = IntegerField()
    alternative_titles = TextField(column_name='alternativeTitles', null=True)
    audio_codec = TextField(null=True)
    audio_language = TextField(null=True)
    failed_attempts = TextField(column_name='failedAttempts', null=True)
    fanart = TextField(null=True)
    forced = TextField(null=True, constraints=[SQL('DEFAULT "False"')])
    format = TextField(null=True)
    hearing_impaired = TextField(null=True)
    imdb_id = TextField(column_name='imdbId', null=True)
    languages = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    overview = TextField(null=True)
    path = TextField(unique=True)
    poster = TextField(null=True)
    radarr_id = IntegerField(column_name='radarrId', null=False, unique=True)
    resolution = TextField(null=True)
    scene_name = TextField(column_name='sceneName', null=True)
    sort_title = TextField(column_name='sortTitle', null=True)
    subtitles = TextField(null=True)
    title = TextField(null=False)
    tmdb_id = TextField(column_name='tmdbId', primary_key=True, null=False)
    video_codec = TextField(null=True)
    year = TextField(null=True)
    movie_file_id = IntegerField(null=True)

    class Meta:
        table_name = 'table_movies'


class TableHistory(BaseModel):
    id = PrimaryKeyField(null=False)
    action = IntegerField(null=False)
    description = TextField(null=False)
    language = TextField(null=True)
    provider = TextField(null=True)
    score = TextField(null=True)
    sonarr_episode_id = ForeignKeyField(TableEpisodes, field='sonarr_episode_id', column_name='sonarrEpisodeId', null=False)
    sonarr_series_id = ForeignKeyField(TableShows, field='sonarr_series_id', column_name='sonarrSeriesId', null=False)
    timestamp = IntegerField(null=False)
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history'


class TableHistoryMovie(BaseModel):
    id = PrimaryKeyField(null=False)
    action = IntegerField(null=False)
    description = TextField(null=False)
    language = TextField(null=True)
    provider = TextField(null=True)
    radarr_id = ForeignKeyField(TableMovies, field='radarr_id', column_name='radarrId', null=False)
    score = TextField(null=True)
    timestamp = IntegerField(null=False)
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history_movie'


class TableSettingsLanguages(BaseModel):
    code2 = TextField(null=False)
    code3 = TextField(null=False, unique=True, primary_key=True)
    code3b = TextField(null=True)
    enabled = IntegerField(null=True)
    name = TextField(null=False)

    class Meta:
        table_name = 'table_settings_languages'


class TableSettingsNotifier(BaseModel):
    enabled = IntegerField(null=False)
    name = TextField(null=False, primary_key=True)
    url = TextField(null=True)

    class Meta:
        table_name = 'table_settings_notifier'


# Database tables creation if they don't exists
models_list = [TableShows, TableEpisodes, TableMovies, TableHistory, TableHistoryMovie, TableSettingsLanguages,
               TableSettingsNotifier, System]
database.create_tables(models_list, safe=True)


# Database migration
migrator = SqliteMigrator(database)

# TableShows migration
table_shows_columns = []
for column in database.get_columns('table_shows'):
    table_shows_columns.append(column.name)
if 'forced' not in table_shows_columns:
    migrate(migrator.add_column('table_shows', 'forced', TableShows.forced))

# TableEpisodes migration
table_episodes_columns = []
for column in database.get_columns('table_episodes'):
    table_episodes_columns.append(column.name)
if 'episode_file_id' not in table_episodes_columns:
    migrate(migrator.add_column('table_episodes', 'episode_file_id', TableEpisodes.episode_file_id))

# TableMovies migration
table_movies_columns = []
for column in database.get_columns('table_movies'):
    table_movies_columns.append(column.name)
if 'forced' not in table_movies_columns:
    migrate(migrator.add_column('table_movies', 'forced', TableMovies.forced))
if 'movie_file_id' not in table_movies_columns:
    migrate(migrator.add_column('table_movies', 'movie_file_id', TableMovies.movie_file_id))


def wal_cleaning():
    database.pragma('wal_checkpoint', 'TRUNCATE')  # Run a checkpoint and merge remaining wal-journal.
    database.wal_autocheckpoint = 50  # Run an automatic checkpoint every 50 write transactions.
