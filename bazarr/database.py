import os
import atexit

from get_args import args
from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase

from helper import path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie

database = SqliteQueueDatabase(
    os.path.join(args.config_dir, 'db', 'bazarr.db'),
    use_gevent=False,  # Use the standard library "threading" module.
    autostart=True,  # The worker thread now must be started manually.
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


class SqliteSequence(BaseModel):
    name = BareField(null=True)
    seq = BareField(null=True)

    class Meta:
        table_name = 'sqlite_sequence'
        primary_key = False


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
    forced = TextField(null=True)
    hearing_impaired = TextField(null=True)
    languages = TextField(null=True)
    overview = TextField(null=True)
    path = TextField(unique=True)
    poster = TextField(null=True)
    sonarr_series_id = IntegerField(column_name='sonarrSeriesId', unique=True)
    sort_title = TextField(column_name='sortTitle', null=True)
    title = TextField()
    tvdb_id = AutoField(column_name='tvdbId')
    year = TextField(null=True)

    class Meta:
        table_name = 'table_shows'


class TableEpisodes(BaseModel):
    audio_codec = TextField(null=True)
    episode = IntegerField()
    failed_attempts = TextField(column_name='failedAttempts', null=True)
    format = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    path = TextField()
    resolution = TextField(null=True)
    scene_name = TextField(null=True)
    season = IntegerField()
    sonarr_episode_id = IntegerField(column_name='sonarrEpisodeId', unique=True)
    sonarr_series_id = ForeignKeyField(TableShows, field='sonarr_series_id', column_name='sonarrSeriesId')
    subtitles = TextField(null=True)
    title = TextField()
    video_codec = TextField(null=True)

    class Meta:
        table_name = 'table_episodes'
        primary_key = False


class TableMovies(BaseModel):
    alternative_titles = TextField(column_name='alternativeTitles', null=True)
    audio_codec = TextField(null=True)
    audio_language = TextField(null=True)
    failed_attempts = TextField(column_name='failedAttempts', null=True)
    fanart = TextField(null=True)
    forced = TextField(null=True)
    format = TextField(null=True)
    hearing_impaired = TextField(null=True)
    imdb_id = TextField(column_name='imdbId', null=True)
    languages = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    overview = TextField(null=True)
    path = TextField(unique=True)
    poster = TextField(null=True)
    radarr_id = IntegerField(column_name='radarrId', unique=True)
    resolution = TextField(null=True)
    scene_name = TextField(column_name='sceneName', null=True)
    sort_title = TextField(column_name='sortTitle', null=True)
    subtitles = TextField(null=True)
    title = TextField()
    tmdb_id = TextField(column_name='tmdbId', primary_key=True)
    video_codec = TextField(null=True)
    year = TextField(null=True)

    class Meta:
        table_name = 'table_movies'


class TableHistory(BaseModel):
    id = IntegerField(null=False)
    action = IntegerField()
    description = TextField()
    language = TextField(null=True)
    provider = TextField(null=True)
    score = TextField(null=True)
    sonarr_episode_id = ForeignKeyField(TableEpisodes, field='sonarr_episode_id', column_name='sonarrEpisodeId')
    sonarr_series_id = ForeignKeyField(TableShows, field='sonarr_series_id', column_name='sonarrSeriesId')
    timestamp = IntegerField()
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history'
        primary_key = False


class TableHistoryMovie(BaseModel):
    id = IntegerField(null=False)
    action = IntegerField()
    description = TextField()
    language = TextField(null=True)
    provider = TextField(null=True)
    radarr_id = ForeignKeyField(TableMovies, field='radarr_id', column_name='radarrId')
    score = TextField(null=True)
    timestamp = IntegerField()
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history_movie'
        primary_key = False


class TableSettingsLanguages(BaseModel):
    code2 = TextField(null=True)
    code3 = TextField(primary_key=True)
    code3b = TextField(null=True)
    enabled = IntegerField(null=True)
    name = TextField()

    class Meta:
        table_name = 'table_settings_languages'


class TableSettingsNotifier(BaseModel):
    enabled = IntegerField(null=True)
    name = TextField(null=True, primary_key=True)
    url = TextField(null=True)

    class Meta:
        table_name = 'table_settings_notifier'


@atexit.register
def _stop_worker_threads():
    database.stop()