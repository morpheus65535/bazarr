# -*- coding: utf-8 -*-
import ast
import atexit
import json
import logging
import os

from dogpile.cache import make_region
from sqlalchemy import create_engine, Column, DateTime, ForeignKey, Integer, LargeBinary, Table, Text, update, delete, \
    select, func
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool

from utilities.path_mappings import path_mappings
from .config import settings, get_array_from
from .get_args import args

logger = logging.getLogger(__name__)

postgresql = settings.postgresql.getboolean('enabled')

region = make_region().configure('dogpile.cache.memory')

if postgresql:
    from sqlalchemy.dialects.postgresql import insert
    # class ReconnectPostgresqlDatabase(ReconnectMixin, PostgresqlDatabase):
    #     reconnect_errors = (
    #         (OperationalError, 'server closed the connection unexpectedly'),
    #     )
    #
    # logger.debug(
    #     f"Connecting to PostgreSQL database: {settings.postgresql.host}:{settings.postgresql.port}/{settings.postgresql.database}")
    # database = ReconnectPostgresqlDatabase(settings.postgresql.database,
    #                                        user=settings.postgresql.username,
    #                                        password=settings.postgresql.password,
    #                                        host=settings.postgresql.host,
    #                                        port=settings.postgresql.port,
    #                                        autocommit=True,
    #                                        autorollback=True,
    #                                        autoconnect=True,
    #                                        )
    # migrator = PostgresqlMigrator(database)
    pass
else:
    from sqlalchemy.dialects.sqlite import insert
    db_path = os.path.join(args.config_dir, 'db', 'bazarr.db')
    logger.debug(f"Connecting to SQLite database: {db_path}")
    engine = create_engine(f'sqlite:///{db_path}', poolclass=NullPool)
    session_factory = sessionmaker(bind=engine)
    database = scoped_session(session_factory)


@atexit.register
def _stop_worker_threads():
    database.remove()


Base = declarative_base()
metadata = Base.metadata


class System(Base):
    __tablename__ = 'system'

    configured = Column(Text, primary_key=True)
    updated = Column(Text)


class TableAnnouncements(Base):
    __tablename__ = 'table_announcements'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    hash = Column(Text, unique=True)
    text = Column(Text)


class TableBlacklist(Base):
    __tablename__ = 'table_blacklist'

    language = Column(Text)
    provider = Column(Text)
    sonarr_episode_id = Column(Integer)
    sonarr_series_id = Column(Integer)
    subs_id = Column(Text)
    timestamp = Column(DateTime, primary_key=True)


class TableBlacklistMovie(Base):
    __tablename__ = 'table_blacklist_movie'

    language = Column(Text)
    provider = Column(Text)
    radarr_id = Column(Integer)
    subs_id = Column(Text)
    timestamp = Column(DateTime, primary_key=True)


class TableCustomScoreProfiles(Base):
    __tablename__ = 'table_custom_score_profiles'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    media = Column(Text)
    score = Column(Integer)


class TableEpisodes(Base):
    __tablename__ = 'table_episodes'

    rowid = Column(Integer, primary_key=True)
    audio_codec = Column(Text)
    audio_language = Column(Text)
    episode = Column(Integer, nullable=False)
    episode_file_id = Column(Integer)
    failedAttempts = Column(Text)
    ffprobe_cache = Column(LargeBinary)
    file_size = Column(Integer)
    format = Column(Text)
    missing_subtitles = Column(Text)
    monitored = Column(Text)
    path = Column(Text, nullable=False)
    resolution = Column(Text)
    sceneName = Column(Text)
    season = Column(Integer, nullable=False)
    sonarrEpisodeId = Column(Integer, nullable=False, unique=True)
    sonarrSeriesId = Column(Integer, nullable=False)
    subtitles = Column(Text)
    title = Column(Text, nullable=False)
    video_codec = Column(Text)


class TableHistory(Base):
    __tablename__ = 'table_history'

    id = Column(Integer, primary_key=True)
    action = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    language = Column(Text)
    provider = Column(Text)
    score = Column(Integer)
    sonarrEpisodeId = Column(Integer, nullable=False)
    sonarrSeriesId = Column(Integer, nullable=False)
    subs_id = Column(Text)
    subtitles_path = Column(Text)
    timestamp = Column(DateTime, nullable=False)
    video_path = Column(Text)


class TableHistoryMovie(Base):
    __tablename__ = 'table_history_movie'

    id = Column(Integer, primary_key=True)
    action = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    language = Column(Text)
    provider = Column(Text)
    radarrId = Column(Integer, nullable=False)
    score = Column(Integer)
    subs_id = Column(Text)
    subtitles_path = Column(Text)
    timestamp = Column(DateTime, nullable=False)
    video_path = Column(Text)


class TableLanguagesProfiles(Base):
    __tablename__ = 'table_languages_profiles'

    profileId = Column(Integer, primary_key=True)
    cutoff = Column(Integer)
    originalFormat = Column(Integer)
    items = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    mustContain = Column(Text)
    mustNotContain = Column(Text)


class TableMovies(Base):
    __tablename__ = 'table_movies'

    rowid = Column(Integer, primary_key=True)
    alternativeTitles = Column(Text)
    audio_codec = Column(Text)
    audio_language = Column(Text)
    failedAttempts = Column(Text)
    fanart = Column(Text)
    ffprobe_cache = Column(LargeBinary)
    file_size = Column(Integer)
    format = Column(Text)
    imdbId = Column(Text)
    missing_subtitles = Column(Text)
    monitored = Column(Text)
    movie_file_id = Column(Integer)
    overview = Column(Text)
    path = Column(Text, nullable=False, unique=True)
    poster = Column(Text)
    profileId = Column(Integer)
    radarrId = Column(Integer, nullable=False, unique=True)
    resolution = Column(Text)
    sceneName = Column(Text)
    sortTitle = Column(Text)
    subtitles = Column(Text)
    tags = Column(Text)
    title = Column(Text, nullable=False)
    tmdbId = Column(Text, nullable=False, unique=True)
    video_codec = Column(Text)
    year = Column(Text)


class TableMoviesRootfolder(Base):
    __tablename__ = 'table_movies_rootfolder'

    accessible = Column(Integer)
    error = Column(Text)
    id = Column(Integer, primary_key=True)
    path = Column(Text)


class TableSettingsLanguages(Base):
    __tablename__ = 'table_settings_languages'

    code3 = Column(Text, primary_key=True)
    code2 = Column(Text)
    code3b = Column(Text)
    enabled = Column(Integer)
    name = Column(Text, nullable=False)


class TableSettingsNotifier(Base):
    __tablename__ = 'table_settings_notifier'

    name = Column(Text, primary_key=True)
    enabled = Column(Integer)
    url = Column(Text)


class TableShows(Base):
    __tablename__ = 'table_shows'

    tvdbId = Column(Integer, primary_key=True)
    alternativeTitles = Column(Text)
    audio_language = Column(Text)
    fanart = Column(Text)
    imdbId = Column(Text)
    monitored = Column(Text)
    overview = Column(Text)
    path = Column(Text, nullable=False, unique=True)
    poster = Column(Text)
    profileId = Column(Integer)
    seriesType = Column(Text)
    sonarrSeriesId = Column(Integer, nullable=False, unique=True)
    sortTitle = Column(Text)
    tags = Column(Text)
    title = Column(Text, nullable=False)
    year = Column(Text)
    alternativeTitle = Column(Text)


class TableShowsRootfolder(Base):
    __tablename__ = 'table_shows_rootfolder'

    accessible = Column(Integer)
    error = Column(Text)
    id = Column(Integer, primary_key=True)
    path = Column(Text)


class TableCustomScoreProfileConditions(Base):
    __tablename__ = 'table_custom_score_profile_conditions'

    id = Column(Integer, primary_key=True)
    profile_id = Column(ForeignKey('table_custom_score_profiles.id'), nullable=False, index=True)
    type = Column(Text)
    value = Column(Text)
    required = Column(Integer, nullable=False)
    negate = Column(Integer, nullable=False)

    profile = relationship('TableCustomScoreProfiles')


def init_db():
    database.begin()

    # Create tables if they don't exist.
    metadata.create_all(engine)

    # add the system table single row if it's not existing
    if not database.query(System).count():
        database.execute(insert(System).values(configured='0', updated='0'))
        database.commit()


def rows_as_list_of_dicts(query):
    try:
        return [dict(row._mapping) for row in query]
    except Exception as e:
        return False


# def migrate_db():
#     table_shows = [t.name for t in database.get_columns('table_shows')]
#     table_episodes = [t.name for t in database.get_columns('table_episodes')]
#     table_movies = [t.name for t in database.get_columns('table_movies')]
#     table_history = [t.name for t in database.get_columns('table_history')]
#     table_history_movie = [t.name for t in database.get_columns('table_history_movie')]
#     table_languages_profiles = [t.name for t in database.get_columns('table_languages_profiles')]
#     if "year" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'year', TextField(null=True)))
#     if "alternativeTitle" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'alternativeTitle', TextField(null=True)))
#     if "tags" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'tags', TextField(default='[]', null=True)))
#     if "seriesType" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'seriesType', TextField(default='""', null=True)))
#     if "imdbId" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'imdbId', TextField(default='""', null=True)))
#     if "profileId" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'profileId', IntegerField(null=True)))
#     if "profileId" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'profileId', IntegerField(null=True)))
#     if "monitored" not in table_shows:
#         migrate(migrator.add_column('table_shows', 'monitored', TextField(null=True)))
#
#     if "format" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'format', TextField(null=True)))
#     if "resolution" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'resolution', TextField(null=True)))
#     if "video_codec" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'video_codec', TextField(null=True)))
#     if "audio_codec" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'audio_codec', TextField(null=True)))
#     if "episode_file_id" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'episode_file_id', IntegerField(null=True)))
#     if "audio_language" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'audio_language', TextField(null=True)))
#     if "file_size" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'file_size', BigIntegerField(default=0, null=True)))
#     if "ffprobe_cache" not in table_episodes:
#         migrate(migrator.add_column('table_episodes', 'ffprobe_cache', BlobField(null=True)))
#
#     if "sortTitle" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'sortTitle', TextField(null=True)))
#     if "year" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'year', TextField(null=True)))
#     if "alternativeTitles" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'alternativeTitles', TextField(null=True)))
#     if "format" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'format', TextField(null=True)))
#     if "resolution" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'resolution', TextField(null=True)))
#     if "video_codec" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'video_codec', TextField(null=True)))
#     if "audio_codec" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'audio_codec', TextField(null=True)))
#     if "imdbId" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'imdbId', TextField(null=True)))
#     if "movie_file_id" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'movie_file_id', IntegerField(null=True)))
#     if "tags" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'tags', TextField(default='[]', null=True)))
#     if "profileId" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'profileId', IntegerField(null=True)))
#     if "file_size" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'file_size', BigIntegerField(default=0, null=True)))
#     if "ffprobe_cache" not in table_movies:
#         migrate(migrator.add_column('table_movies', 'ffprobe_cache', BlobField(null=True)))
#
#     if "video_path" not in table_history:
#         migrate(migrator.add_column('table_history', 'video_path', TextField(null=True)))
#     if "language" not in table_history:
#         migrate(migrator.add_column('table_history', 'language', TextField(null=True)))
#     if "provider" not in table_history:
#         migrate(migrator.add_column('table_history', 'provider', TextField(null=True)))
#     if "score" not in table_history:
#         migrate(migrator.add_column('table_history', 'score', TextField(null=True)))
#     if "subs_id" not in table_history:
#         migrate(migrator.add_column('table_history', 'subs_id', TextField(null=True)))
#     if "subtitles_path" not in table_history:
#         migrate(migrator.add_column('table_history', 'subtitles_path', TextField(null=True)))
#
#     if "video_path" not in table_history_movie:
#         migrate(migrator.add_column('table_history_movie', 'video_path', TextField(null=True)))
#     if "language" not in table_history_movie:
#         migrate(migrator.add_column('table_history_movie', 'language', TextField(null=True)))
#     if "provider" not in table_history_movie:
#         migrate(migrator.add_column('table_history_movie', 'provider', TextField(null=True)))
#     if "score" not in table_history_movie:
#         migrate(migrator.add_column('table_history_movie', 'score', TextField(null=True)))
#     if "subs_id" not in table_history_movie:
#         migrate(migrator.add_column('table_history_movie', 'subs_id', TextField(null=True)))
#     if "subtitles_path" not in table_history_movie:
#         migrate(migrator.add_column('table_history_movie', 'subtitles_path', TextField(null=True)))
#
#     if "mustContain" not in table_languages_profiles:
#         migrate(migrator.add_column('table_languages_profiles', 'mustContain', TextField(null=True)))
#     if "mustNotContain" not in table_languages_profiles:
#         migrate(migrator.add_column('table_languages_profiles', 'mustNotContain', TextField(null=True)))
#     if "originalFormat" not in table_languages_profiles:
#         migrate(migrator.add_column('table_languages_profiles', 'originalFormat', BooleanField(null=True)))
#
#     if "languages" in table_shows:
#         migrate(migrator.drop_column('table_shows', 'languages'))
#     if "hearing_impaired" in table_shows:
#         migrate(migrator.drop_column('table_shows', 'hearing_impaired'))
#
#     if "languages" in table_movies:
#         migrate(migrator.drop_column('table_movies', 'languages'))
#     if "hearing_impaired" in table_movies:
#         migrate(migrator.drop_column('table_movies', 'hearing_impaired'))
#     if not any(
#             x
#             for x in database.get_columns('table_blacklist')
#             if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
#     ):
#         migrate(migrator.alter_column_type('table_blacklist', 'timestamp', DateTimeField(default=datetime.now)))
#         update = TableBlacklist.select()
#         for item in update:
#             item.update({"timestamp": datetime.fromtimestamp(int(item.timestamp))}).execute()
#
#     if not any(
#             x
#             for x in database.get_columns('table_blacklist_movie')
#             if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
#     ):
#         migrate(migrator.alter_column_type('table_blacklist_movie', 'timestamp', DateTimeField(default=datetime.now)))
#         update = TableBlacklistMovie.select()
#         for item in update:
#             item.update({"timestamp": datetime.fromtimestamp(int(item.timestamp))}).execute()
#
#     if not any(
#             x for x in database.get_columns('table_history') if x.name == "score" and x.data_type.lower() == "integer"):
#         migrate(migrator.alter_column_type('table_history', 'score', IntegerField(null=True)))
#     if not any(
#             x
#             for x in database.get_columns('table_history')
#             if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
#     ):
#         migrate(migrator.alter_column_type('table_history', 'timestamp', DateTimeField(default=datetime.now)))
#         update = TableHistory.select()
#         list_to_update = []
#         for i, item in enumerate(update):
#             item.timestamp = datetime.fromtimestamp(int(item.timestamp))
#             list_to_update.append(item)
#             if i % 100 == 0:
#                 TableHistory.bulk_update(list_to_update, fields=[TableHistory.timestamp])
#                 list_to_update = []
#         if list_to_update:
#             TableHistory.bulk_update(list_to_update, fields=[TableHistory.timestamp])
#
#     if not any(x for x in database.get_columns('table_history_movie') if
#                x.name == "score" and x.data_type.lower() == "integer"):
#         migrate(migrator.alter_column_type('table_history_movie', 'score', IntegerField(null=True)))
#     if not any(
#             x
#             for x in database.get_columns('table_history_movie')
#             if x.name == "timestamp" and x.data_type in ["DATETIME", "timestamp without time zone"]
#     ):
#         migrate(migrator.alter_column_type('table_history_movie', 'timestamp', DateTimeField(default=datetime.now)))
#         update = TableHistoryMovie.select()
#         list_to_update = []
#         for i, item in enumerate(update):
#             item.timestamp = datetime.fromtimestamp(int(item.timestamp))
#             list_to_update.append(item)
#             if i % 100 == 0:
#                 TableHistoryMovie.bulk_update(list_to_update, fields=[TableHistoryMovie.timestamp])
#                 list_to_update = []
#         if list_to_update:
#             TableHistoryMovie.bulk_update(list_to_update, fields=[TableHistoryMovie.timestamp])
#     # if not any(x for x in database.get_columns('table_movies') if x.name == "monitored" and x.data_type == "BOOLEAN"):
#     #     migrate(migrator.alter_column_type('table_movies', 'monitored', BooleanField(null=True)))
#
#     if database.get_columns('table_settings_providers'):
#         database.execute_sql('drop table if exists table_settings_providers;')
#
#     if "alternateTitles" in table_shows:
#         migrate(migrator.rename_column('table_shows', 'alternateTitles', "alternativeTitles"))
#
#     if "scene_name" in table_episodes:
#         migrate(migrator.rename_column('table_episodes', 'scene_name', "sceneName"))


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
    profile_id_list = rows_as_list_of_dicts(database.query(TableLanguagesProfiles.profileId,
                                                           TableLanguagesProfiles.name,
                                                           TableLanguagesProfiles.cutoff,
                                                           TableLanguagesProfiles.items,
                                                           TableLanguagesProfiles.mustContain,
                                                           TableLanguagesProfiles.mustNotContain,
                                                           TableLanguagesProfiles.originalFormat).all())
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
        data = database.query(TableShows.profileId).where(TableShows.sonarrSeriesId == series_id).first()
        if data:
            return data.profileId
    elif episode_id:
        data = database.query(TableShows.profileId)\
            .join(TableEpisodes, TableShows.sonarrSeriesId == TableEpisodes.sonarrSeriesId)\
            .where(TableEpisodes.sonarrEpisodeId == episode_id)\
            .first()
        if data:
            return data.profileId

    elif movie_id:
        data = database.query(TableMovies.profileId).where(TableMovies.radarrId == movie_id).first()
        if data:
            return data.profileId

    return None


def convert_list_to_clause(arr: list):
    if isinstance(arr, list):
        return f"({','.join(str(x) for x in arr)})"
    else:
        return ""
