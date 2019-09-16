import os
import atexit

from get_args import args
from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase

from helper import path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie

database = SqliteQueueDatabase(
    None,
    use_gevent=False,
    autostart=False,
    queue_max_size=256,  # Max. # of pending writes that can accumulate.
    results_timeout=30.0)  # Max. time to wait for query to be executed.


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
    configured = TextField()
    updated = TextField()

    class Meta:
        table_name = 'system'
        primary_key = False


class TableShows(BaseModel):
    alternate_titles = TextField(column_name='alternateTitles')
    audio_language = TextField()
    fanart = TextField()
    forced = TextField()
    hearing_impaired = TextField()
    languages = TextField()
    overview = TextField()
    path = TextField(unique=True)
    poster = TextField()
    sonarr_series_id = IntegerField(column_name='sonarrSeriesId', unique=True)
    sort_title = TextField(column_name='sortTitle')
    title = TextField()
    tvdb_id = AutoField(column_name='tvdbId')
    year = TextField()

    class Meta:
        table_name = 'table_shows'


class TableEpisodes(BaseModel):
    audio_codec = TextField()
    episode = IntegerField()
    failed_attempts = TextField(column_name='failedAttempts')
    format = TextField()
    missing_subtitles = TextField()
    monitored = TextField()
    path = TextField()
    resolution = TextField()
    scene_name = TextField()
    season = IntegerField()
    sonarr_episode_id = IntegerField(column_name='sonarrEpisodeId', unique=True)
    sonarr_series_id = ForeignKeyField(TableShows, field='sonarr_series_id', column_name='sonarrSeriesId')
    subtitles = TextField()
    title = TextField()
    video_codec = TextField()

    class Meta:
        table_name = 'table_episodes'
        primary_key = False


class TableMovies(BaseModel):
    alternative_titles = TextField(column_name='alternativeTitles')
    audio_codec = TextField()
    audio_language = TextField()
    failed_attempts = TextField(column_name='failedAttempts')
    fanart = TextField()
    forced = TextField()
    format = TextField()
    hearing_impaired = TextField()
    imdb_id = TextField(column_name='imdbId')
    languages = TextField()
    missing_subtitles = TextField()
    monitored = TextField()
    overview = TextField()
    path = TextField(unique=True)
    poster = TextField()
    radarr_id = IntegerField(column_name='radarrId', unique=True)
    resolution = TextField()
    scene_name = TextField(column_name='sceneName')
    sort_title = TextField(column_name='sortTitle')
    subtitles = TextField()
    title = TextField()
    tmdb_id = TextField(column_name='tmdbId', primary_key=True)
    video_codec = TextField()
    year = TextField()

    class Meta:
        table_name = 'table_movies'


class TableHistory(BaseModel):
    id = IntegerField(null=False)
    action = IntegerField()
    description = TextField()
    language = TextField(null=False)
    provider = TextField(null=False)
    score = TextField(null=False)
    sonarr_episode_id = ForeignKeyField(TableEpisodes, field='sonarr_episode_id', column_name='sonarrEpisodeId')
    sonarr_series_id = ForeignKeyField(TableShows, field='sonarr_series_id', column_name='sonarrSeriesId')
    timestamp = IntegerField()
    video_path = TextField(null=False)

    class Meta:
        table_name = 'table_history'
        primary_key = False


class TableHistoryMovie(BaseModel):
    id = IntegerField(null=False)
    action = IntegerField()
    description = TextField()
    language = TextField(null=False)
    provider = TextField(null=False)
    radarr_id = ForeignKeyField(TableMovies, field='radarr_id', column_name='radarrId')
    score = TextField(null=False)
    timestamp = IntegerField()
    video_path = TextField(null=False)

    class Meta:
        table_name = 'table_history_movie'
        primary_key = False


class TableSettingsLanguages(BaseModel):
    code2 = TextField()
    code3 = TextField(primary_key=True)
    code3b = TextField()
    enabled = IntegerField()
    name = TextField()

    class Meta:
        table_name = 'table_settings_languages'


class TableSettingsNotifier(BaseModel):
    enabled = IntegerField()
    name = TextField(primary_key=True)
    url = TextField()

    class Meta:
        table_name = 'table_settings_notifier'


def database_init():
    database.init(os.path.join(args.config_dir, 'db', 'bazarr.db'))
    database.start()
    database.connect()

    database.pragma('wal_checkpoint', 'TRUNCATE')  # Run a checkpoint and merge remaining wal-journal.
    database.cache_size = -1024  # Number of KB of cache for wal-journal.
                                 # Must be negative because positive means number of pages.
    database.wal_autocheckpoint = 50  # Run an automatic checkpoint every 50 write transactions.

    models_list = [TableShows, TableEpisodes, TableMovies, TableHistory, TableHistoryMovie, TableSettingsLanguages,
                   TableSettingsNotifier, System]

    database.create_tables(models_list, safe=True)


def wal_cleaning():
    database.pragma('wal_checkpoint', 'TRUNCATE')  # Run a checkpoint and merge remaining wal-journal.
    database.wal_autocheckpoint = 50  # Run an automatic checkpoint every 50 write transactions.
