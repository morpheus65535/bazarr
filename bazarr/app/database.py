# -*- coding: utf-8 -*-
import ast
import atexit
import json
import logging
import os
import time
from datetime import datetime

from dogpile.cache import make_region
from peewee import Model, AutoField, TextField, IntegerField, ForeignKeyField, BlobField, BooleanField, BigIntegerField, \
    DateTimeField, OperationalError, PostgresqlDatabase
from playhouse.migrate import PostgresqlMigrator
from playhouse.migrate import SqliteMigrator, migrate
from playhouse.shortcuts import ThreadSafeDatabaseMetadata, ReconnectMixin
from playhouse.sqlite_ext import RowIDField
from playhouse.sqliteq import SqliteQueueDatabase

from utilities.path_mappings import path_mappings
from .config import settings, get_array_from
from .get_args import args

logger = logging.getLogger(__name__)

postgresql = settings.postgresql.getboolean('enabled')

region = make_region().configure('dogpile.cache.memory')

if postgresql:
    class ReconnectPostgresqlDatabase(ReconnectMixin, PostgresqlDatabase):
        reconnect_errors = (
            (OperationalError, 'server closed the connection unexpectedly'),
        )


    logger.debug(
        f"Connecting to PostgreSQL database: {settings.postgresql.host}:{settings.postgresql.port}/{settings.postgresql.database}")
    database = ReconnectPostgresqlDatabase(settings.postgresql.database,
                                           user=settings.postgresql.username,
                                           password=settings.postgresql.password,
                                           host=settings.postgresql.host,
                                           port=settings.postgresql.port,
                                           autocommit=True,
                                           autorollback=True,
                                           autoconnect=True,
                                           )
    migrator = PostgresqlMigrator(database)
else:
    db_path = os.path.join(args.config_dir, 'db', 'bazarr.db')
    logger.debug(f"Connecting to SQLite database: {db_path}")
    database = SqliteQueueDatabase(db_path,
                                   use_gevent=False,
                                   autostart=True,
                                   queue_max_size=256)
    migrator = SqliteMigrator(database)


@atexit.register
def _stop_worker_threads():
    if not postgresql:
        database.stop()


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database
        model_metadata_class = ThreadSafeDatabaseMetadata


class System(BaseModel):
    configured = TextField(null=True)
    updated = TextField(null=True)

    class Meta:
        table_name = 'system'
        primary_key = False


class TableBlacklist(BaseModel):
    language = TextField(null=True)
    provider = TextField(null=True)
    sonarr_episode_id = IntegerField(null=True)
    sonarr_series_id = IntegerField(null=True)
    subs_id = TextField(null=True)
    timestamp = DateTimeField(null=True)

    class Meta:
        table_name = 'table_blacklist'
        primary_key = False


class TableBlacklistMovie(BaseModel):
    language = TextField(null=True)
    provider = TextField(null=True)
    radarr_id = IntegerField(null=True)
    subs_id = TextField(null=True)
    timestamp = DateTimeField(null=True)

    class Meta:
        table_name = 'table_blacklist_movie'
        primary_key = False


class TableEpisodes(BaseModel):
    rowid = RowIDField()
    audio_codec = TextField(null=True)
    audio_language = TextField(null=True)
    episode = IntegerField()
    episode_file_id = IntegerField(null=True)
    failedAttempts = TextField(null=True)
    ffprobe_cache = BlobField(null=True)
    file_size = BigIntegerField(default=0, null=True)
    format = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    path = TextField()
    resolution = TextField(null=True)
    sceneName = TextField(null=True)
    season = IntegerField()
    sonarrEpisodeId = IntegerField(unique=True)
    sonarrSeriesId = IntegerField()
    subtitles = TextField(null=True)
    title = TextField()
    video_codec = TextField(null=True)

    class Meta:
        table_name = 'table_episodes'
        primary_key = False

    @classmethod
    def need_update(cls, episode):
        try:
            data = cls.get(cls.sonarrEpisodeId == episode['sonarrEpisodeId']).__data__
        except cls.DoesNotExist:
            return True
        for key, value in data.items():
            if not episode.get(key):
                continue
            if value != episode[key]:
                return True
        return False


class TableHistory(BaseModel):
    action = IntegerField()
    description = TextField()
    id = AutoField()
    language = TextField(null=True)
    provider = TextField(null=True)
    score = IntegerField(null=True)
    sonarrEpisodeId = IntegerField()
    sonarrSeriesId = IntegerField()
    subs_id = TextField(null=True)
    subtitles_path = TextField(null=True)
    timestamp = DateTimeField()
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history'


class TableHistoryMovie(BaseModel):
    action = IntegerField()
    description = TextField()
    id = AutoField()
    language = TextField(null=True)
    provider = TextField(null=True)
    radarrId = IntegerField()
    score = IntegerField(null=True)
    subs_id = TextField(null=True)
    subtitles_path = TextField(null=True)
    timestamp = DateTimeField()
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history_movie'


class TableLanguagesProfiles(BaseModel):
    cutoff = IntegerField(null=True)
    originalFormat = BooleanField(null=True)
    items = TextField()
    name = TextField()
    profileId = AutoField()
    mustContain = TextField(null=True)
    mustNotContain = TextField(null=True)

    class Meta:
        table_name = 'table_languages_profiles'


class TableMovies(BaseModel):
    rowid = RowIDField()
    alternativeTitles = TextField(null=True)
    audio_codec = TextField(null=True)
    audio_language = TextField(null=True)
    failedAttempts = TextField(null=True)
    fanart = TextField(null=True)
    ffprobe_cache = BlobField(null=True)
    file_size = BigIntegerField(default=0, null=True)
    format = TextField(null=True)
    imdbId = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    movie_file_id = IntegerField(null=True)
    overview = TextField(null=True)
    path = TextField(unique=True)
    poster = TextField(null=True)
    profileId = IntegerField(null=True)
    radarrId = IntegerField(unique=True)
    resolution = TextField(null=True)
    sceneName = TextField(null=True)
    sortTitle = TextField(null=True)
    subtitles = TextField(null=True)
    tags = TextField(null=True)
    title = TextField()
    tmdbId = TextField(unique=True)
    video_codec = TextField(null=True)
    year = TextField(null=True)

    class Meta:
        table_name = 'table_movies'


class TableMoviesRootfolder(BaseModel):
    accessible = IntegerField(null=True)
    error = TextField(null=True)
    id = IntegerField(null=True)
    path = TextField(null=True)

    class Meta:
        table_name = 'table_movies_rootfolder'
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


class TableShows(BaseModel):
    alternativeTitles = TextField(null=True)
    audio_language = TextField(null=True)
    fanart = TextField(null=True)
    imdbId = TextField(default='""', null=True)
    monitored = TextField(null=True)
    overview = TextField(null=True)
    path = TextField(unique=True)
    poster = TextField(null=True)
    profileId = IntegerField(null=True)
    seriesType = TextField(null=True)
    sonarrSeriesId = IntegerField(unique=True)
    sortTitle = TextField(null=True)
    tags = TextField(null=True)
    title = TextField()
    tvdbId = AutoField()
    year = TextField(null=True)

    class Meta:
        table_name = 'table_shows'

    @classmethod
    def need_update(cls, show):
        try:
            data = cls.get(cls.sonarrSeriesId == show['sonarrSeriesId']).__data__
        except cls.DoesNotExist:
            return
        for key, value in data.items():
            if not show.get(key):
                continue
            if value != show[key]:
                return True
        return False


class TableShowsRootfolder(BaseModel):
    accessible = IntegerField(null=True)
    error = TextField(null=True)
    id = IntegerField(null=True)
    path = TextField(null=True)

    class Meta:
        table_name = 'table_shows_rootfolder'
        primary_key = False


class TableCustomScoreProfiles(BaseModel):
    id = AutoField()
    name = TextField(null=True)
    media = TextField(null=True)
    score = IntegerField(null=True)

    class Meta:
        table_name = 'table_custom_score_profiles'


class TableCustomScoreProfileConditions(BaseModel):
    profile_id = ForeignKeyField(TableCustomScoreProfiles, to_field="id")
    type = TextField(null=True)  # provider, uploader, regex, etc
    value = TextField(null=True)  # opensubtitles, jane_doe, [a-z], etc
    required = BooleanField(default=False)
    negate = BooleanField(default=False)

    class Meta:
        table_name = 'table_custom_score_profile_conditions'


class TableAnnouncements(BaseModel):
    timestamp = DateTimeField()
    hash = TextField(null=True, unique=True)
    text = TextField(null=True)

    class Meta:
        table_name = 'table_announcements'


def init_db():
    # Create tables if they don't exists.
    database.create_tables([System,
                            TableBlacklist,
                            TableBlacklistMovie,
                            TableEpisodes,
                            TableHistory,
                            TableHistoryMovie,
                            TableLanguagesProfiles,
                            TableMovies,
                            TableMoviesRootfolder,
                            TableSettingsLanguages,
                            TableSettingsNotifier,
                            TableShows,
                            TableShowsRootfolder,
                            TableCustomScoreProfiles,
                            TableCustomScoreProfileConditions,
                            TableAnnouncements])

    # add the system table single row if it's not existing
    # we must retry until the tables are created
    tables_created = False
    while not tables_created:
        try:
            if not System.select().count():
                System.insert({System.configured: '0', System.updated: '0'}).execute()
        except Exception:
            time.sleep(0.1)
        else:
            tables_created = True


def migrate_db():
    table_shows = [t.name for t in database.get_columns('table_shows')]
    table_episodes = [t.name for t in database.get_columns('table_episodes')]
    table_movies = [t.name for t in database.get_columns('table_movies')]
    table_history = [t.name for t in database.get_columns('table_history')]
    table_history_movie = [t.name for t in database.get_columns('table_history_movie')]
    table_languages_profiles = [t.name for t in database.get_columns('table_languages_profiles')]
    if "year" not in table_shows:
        migrate(migrator.add_column('table_shows', 'year', TextField(null=True)))
    if "alternativeTitle" not in table_shows:
        migrate(migrator.add_column('table_shows', 'alternativeTitle', TextField(null=True)))
    if "tags" not in table_shows:
        migrate(migrator.add_column('table_shows', 'tags', TextField(default='[]', null=True)))
    if "seriesType" not in table_shows:
        migrate(migrator.add_column('table_shows', 'seriesType', TextField(default='""', null=True)))
    if "imdbId" not in table_shows:
        migrate(migrator.add_column('table_shows', 'imdbId', TextField(default='""', null=True)))
    if "profileId" not in table_shows:
        migrate(migrator.add_column('table_shows', 'profileId', IntegerField(null=True)))
    if "profileId" not in table_shows:
        migrate(migrator.add_column('table_shows', 'profileId', IntegerField(null=True)))
    if "monitored" not in table_shows:
        migrate(migrator.add_column('table_shows', 'monitored', TextField(null=True)))

    if "format" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'format', TextField(null=True)))
    if "resolution" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'resolution', TextField(null=True)))
    if "video_codec" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'video_codec', TextField(null=True)))
    if "audio_codec" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'audio_codec', TextField(null=True)))
    if "episode_file_id" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'episode_file_id', IntegerField(null=True)))
    if "audio_language" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'audio_language', TextField(null=True)))
    if "file_size" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'file_size', BigIntegerField(default=0, null=True)))
    if "ffprobe_cache" not in table_episodes:
        migrate(migrator.add_column('table_episodes', 'ffprobe_cache', BlobField(null=True)))

    if "sortTitle" not in table_movies:
        migrate(migrator.add_column('table_movies', 'sortTitle', TextField(null=True)))
    if "year" not in table_movies:
        migrate(migrator.add_column('table_movies', 'year', TextField(null=True)))
    if "alternativeTitles" not in table_movies:
        migrate(migrator.add_column('table_movies', 'alternativeTitles', TextField(null=True)))
    if "format" not in table_movies:
        migrate(migrator.add_column('table_movies', 'format', TextField(null=True)))
    if "resolution" not in table_movies:
        migrate(migrator.add_column('table_movies', 'resolution', TextField(null=True)))
    if "video_codec" not in table_movies:
        migrate(migrator.add_column('table_movies', 'video_codec', TextField(null=True)))
    if "audio_codec" not in table_movies:
        migrate(migrator.add_column('table_movies', 'audio_codec', TextField(null=True)))
    if "imdbId" not in table_movies:
        migrate(migrator.add_column('table_movies', 'imdbId', TextField(null=True)))
    if "movie_file_id" not in table_movies:
        migrate(migrator.add_column('table_movies', 'movie_file_id', IntegerField(null=True)))
    if "tags" not in table_movies:
        migrate(migrator.add_column('table_movies', 'tags', TextField(default='[]', null=True)))
    if "profileId" not in table_movies:
        migrate(migrator.add_column('table_movies', 'profileId', IntegerField(null=True)))
    if "file_size" not in table_movies:
        migrate(migrator.add_column('table_movies', 'file_size', BigIntegerField(default=0, null=True)))
    if "ffprobe_cache" not in table_movies:
        migrate(migrator.add_column('table_movies', 'ffprobe_cache', BlobField(null=True)))

    if "video_path" not in table_history:
        migrate(migrator.add_column('table_history', 'video_path', TextField(null=True)))
    if "language" not in table_history:
        migrate(migrator.add_column('table_history', 'language', TextField(null=True)))
    if "provider" not in table_history:
        migrate(migrator.add_column('table_history', 'provider', TextField(null=True)))
    if "score" not in table_history:
        migrate(migrator.add_column('table_history', 'score', TextField(null=True)))
    if "subs_id" not in table_history:
        migrate(migrator.add_column('table_history', 'subs_id', TextField(null=True)))
    if "subtitles_path" not in table_history:
        migrate(migrator.add_column('table_history', 'subtitles_path', TextField(null=True)))

    if "video_path" not in table_history_movie:
        migrate(migrator.add_column('table_history_movie', 'video_path', TextField(null=True)))
    if "language" not in table_history_movie:
        migrate(migrator.add_column('table_history_movie', 'language', TextField(null=True)))
    if "provider" not in table_history_movie:
        migrate(migrator.add_column('table_history_movie', 'provider', TextField(null=True)))
    if "score" not in table_history_movie:
        migrate(migrator.add_column('table_history_movie', 'score', TextField(null=True)))
    if "subs_id" not in table_history_movie:
        migrate(migrator.add_column('table_history_movie', 'subs_id', TextField(null=True)))
    if "subtitles_path" not in table_history_movie:
        migrate(migrator.add_column('table_history_movie', 'subtitles_path', TextField(null=True)))

    if "mustContain" not in table_languages_profiles:
        migrate(migrator.add_column('table_languages_profiles', 'mustContain', TextField(null=True)))
    if "mustNotContain" not in table_languages_profiles:
        migrate(migrator.add_column('table_languages_profiles', 'mustNotContain', TextField(null=True)))
    if "originalFormat" not in table_languages_profiles:
        migrate(migrator.add_column('table_languages_profiles', 'originalFormat', BooleanField(null=True)))

    if "languages" in table_shows:
        migrate(migrator.drop_column('table_shows', 'languages'))
    if "hearing_impaired" in table_shows:
        migrate(migrator.drop_column('table_shows', 'hearing_impaired'))

    if "languages" in table_movies:
        migrate(migrator.drop_column('table_movies', 'languages'))
    if "hearing_impaired" in table_movies:
        migrate(migrator.drop_column('table_movies', 'hearing_impaired'))
    if not any(
            x
            for x in database.get_columns('table_blacklist')
            if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
    ):
        migrate(migrator.alter_column_type('table_blacklist', 'timestamp', DateTimeField(default=datetime.now)))
        update = TableBlacklist.select()
        for item in update:
            item.update({"timestamp": datetime.fromtimestamp(int(item.timestamp))}).execute()

    if not any(
            x
            for x in database.get_columns('table_blacklist_movie')
            if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
    ):
        migrate(migrator.alter_column_type('table_blacklist_movie', 'timestamp', DateTimeField(default=datetime.now)))
        update = TableBlacklistMovie.select()
        for item in update:
            item.update({"timestamp": datetime.fromtimestamp(int(item.timestamp))}).execute()

    if not any(
            x for x in database.get_columns('table_history') if x.name == "score" and x.data_type.lower() == "integer"):
        migrate(migrator.alter_column_type('table_history', 'score', IntegerField(null=True)))
    if not any(
            x
            for x in database.get_columns('table_history')
            if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
    ):
        migrate(migrator.alter_column_type('table_history', 'timestamp', DateTimeField(default=datetime.now)))
        update = TableHistory.select()
        list_to_update = []
        for i, item in enumerate(update):
            item.timestamp = datetime.fromtimestamp(int(item.timestamp))
            list_to_update.append(item)
            if i % 100 == 0:
                TableHistory.bulk_update(list_to_update, fields=[TableHistory.timestamp])
                list_to_update = []
        if list_to_update:
            TableHistory.bulk_update(list_to_update, fields=[TableHistory.timestamp])

    if not any(x for x in database.get_columns('table_history_movie') if
               x.name == "score" and x.data_type.lower() == "integer"):
        migrate(migrator.alter_column_type('table_history_movie', 'score', IntegerField(null=True)))
    if not any(
            x
            for x in database.get_columns('table_history_movie')
            if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
    ):
        migrate(migrator.alter_column_type('table_history_movie', 'timestamp', DateTimeField(default=datetime.now)))
        update = TableHistoryMovie.select()
        list_to_update = []
        for i, item in enumerate(update):
            item.timestamp = datetime.fromtimestamp(int(item.timestamp))
            list_to_update.append(item)
            if i % 100 == 0:
                TableHistoryMovie.bulk_update(list_to_update, fields=[TableHistoryMovie.timestamp])
                list_to_update = []
        if list_to_update:
            TableHistoryMovie.bulk_update(list_to_update, fields=[TableHistoryMovie.timestamp])
    # if not any(x for x in database.get_columns('table_movies') if x.name == "monitored" and x.data_type == "BOOLEAN"):
    #     migrate(migrator.alter_column_type('table_movies', 'monitored', BooleanField(null=True)))

    if database.get_columns('table_settings_providers'):
        database.execute_sql('drop table if exists table_settings_providers;')

    if "alternateTitles" in table_shows:
        migrate(migrator.rename_column('table_shows', 'alternateTitles', "alternativeTitles"))

    if "scene_name" in table_episodes:
        migrate(migrator.rename_column('table_episodes', 'scene_name', "sceneName"))


class SqliteDictPathMapper:
    def __init__(self):
        pass

    @staticmethod
    def path_replace(values_dict):
        if type(values_dict) is list:
            for item in values_dict:
                item['path'] = path_mappings.path_replace(item['path'])
        elif type(values_dict) is dict:
            values_dict['path'] = path_mappings.path_replace(values_dict['path'])
        else:
            return path_mappings.path_replace(values_dict)

    @staticmethod
    def path_replace_movie(values_dict):
        if type(values_dict) is list:
            for item in values_dict:
                item['path'] = path_mappings.path_replace_movie(item['path'])
        elif type(values_dict) is dict:
            values_dict['path'] = path_mappings.path_replace_movie(values_dict['path'])
        else:
            return path_mappings.path_replace_movie(values_dict)


dict_mapper = SqliteDictPathMapper()


def get_exclusion_clause(exclusion_type):
    where_clause = []
    if exclusion_type == 'series':
        tagsList = ast.literal_eval(settings.sonarr.excluded_tags)
        for tag in tagsList:
            where_clause.append(~(TableShows.tags.contains("\'" + tag + "\'")))
    else:
        tagsList = ast.literal_eval(settings.radarr.excluded_tags)
        for tag in tagsList:
            where_clause.append(~(TableMovies.tags.contains("\'" + tag + "\'")))

    if exclusion_type == 'series':
        monitoredOnly = settings.sonarr.getboolean('only_monitored')
        if monitoredOnly:
            where_clause.append((TableEpisodes.monitored == True))  # noqa E712
            where_clause.append((TableShows.monitored == True))  # noqa E712
    else:
        monitoredOnly = settings.radarr.getboolean('only_monitored')
        if monitoredOnly:
            where_clause.append((TableMovies.monitored == True))  # noqa E712

    if exclusion_type == 'series':
        typesList = get_array_from(settings.sonarr.excluded_series_types)
        for item in typesList:
            where_clause.append((TableShows.seriesType != item))

        exclude_season_zero = settings.sonarr.getboolean('exclude_season_zero')
        if exclude_season_zero:
            where_clause.append((TableEpisodes.season != 0))

    return where_clause


@region.cache_on_arguments()
def update_profile_id_list():
    profile_id_list = TableLanguagesProfiles.select(TableLanguagesProfiles.profileId,
                                                    TableLanguagesProfiles.name,
                                                    TableLanguagesProfiles.cutoff,
                                                    TableLanguagesProfiles.items,
                                                    TableLanguagesProfiles.mustContain,
                                                    TableLanguagesProfiles.mustNotContain,
                                                    TableLanguagesProfiles.originalFormat).dicts()
    profile_id_list = list(profile_id_list)
    for profile in profile_id_list:
        profile['items'] = json.loads(profile['items'])
        profile['mustContain'] = ast.literal_eval(profile['mustContain']) if profile['mustContain'] else []
        profile['mustNotContain'] = ast.literal_eval(profile['mustNotContain']) if profile['mustNotContain'] else []

    return profile_id_list


def get_profiles_list(profile_id=None):
    profile_id_list = update_profile_id_list()

    if profile_id and profile_id != 'null':
        for profile in profile_id_list:
            if profile['profileId'] == profile_id:
                return profile
    else:
        return profile_id_list


def get_desired_languages(profile_id):
    languages = []
    profile_id_list = update_profile_id_list()

    if profile_id and profile_id != 'null':
        for profile in profile_id_list:
            profileId, name, cutoff, items, mustContain, mustNotContain, originalFormat = profile.values()
            try:
                profile_id_int = int(profile_id)
            except ValueError:
                continue
            else:
                if profileId == profile_id_int:
                    languages = [x['language'] for x in items]
                    break

    return languages


def get_profile_id_name(profile_id):
    name_from_id = None
    profile_id_list = update_profile_id_list()

    if profile_id and profile_id != 'null':
        for profile in profile_id_list:
            profileId, name, cutoff, items, mustContain, mustNotContain, originalFormat = profile.values()
            if profileId == int(profile_id):
                name_from_id = name
                break

    return name_from_id


def get_profile_cutoff(profile_id):
    cutoff_language = None
    profile_id_list = update_profile_id_list()

    if profile_id and profile_id != 'null':
        cutoff_language = []
        for profile in profile_id_list:
            profileId, name, cutoff, items, mustContain, mustNotContain, originalFormat = profile.values()
            if cutoff:
                if profileId == int(profile_id):
                    for item in items:
                        if item['id'] == cutoff:
                            return [item]
                        elif cutoff == 65535:
                            cutoff_language.append(item)

        if not len(cutoff_language):
            cutoff_language = None

    return cutoff_language


def get_audio_profile_languages(audio_languages_list_str):
    from languages.get_languages import alpha2_from_language, alpha3_from_language, language_from_alpha2
    audio_languages = []

    und_default_language = language_from_alpha2(settings.general.default_und_audio_lang)

    try:
        audio_languages_list = ast.literal_eval(audio_languages_list_str or '[]')
    except ValueError:
        pass
    else:
        for language in audio_languages_list:
            if language:
                audio_languages.append(
                    {"name": language,
                     "code2": alpha2_from_language(language) or None,
                     "code3": alpha3_from_language(language) or None}
                )
            else:
                if und_default_language:
                    logging.debug(f"Undefined language audio track treated as {und_default_language}")
                    audio_languages.append(
                        {"name": und_default_language,
                         "code2": alpha2_from_language(und_default_language) or None,
                         "code3": alpha3_from_language(und_default_language) or None}
                    )

    return audio_languages


def get_profile_id(series_id=None, episode_id=None, movie_id=None):
    if series_id:
        data = TableShows.select(TableShows.profileId) \
            .where(TableShows.sonarrSeriesId == series_id) \
            .get_or_none()
        if data:
            return data.profileId
    elif episode_id:
        data = TableShows.select(TableShows.profileId) \
            .join(TableEpisodes, on=(TableShows.sonarrSeriesId == TableEpisodes.sonarrSeriesId)) \
            .where(TableEpisodes.sonarrEpisodeId == episode_id) \
            .get_or_none()
        if data:
            return data.profileId

    elif movie_id:
        data = TableMovies.select(TableMovies.profileId) \
            .where(TableMovies.radarrId == movie_id) \
            .get_or_none()
        if data:
            return data.profileId

    return None


def convert_list_to_clause(arr: list):
    if isinstance(arr, list):
        return f"({','.join(str(x) for x in arr)})"
    else:
        return ""
