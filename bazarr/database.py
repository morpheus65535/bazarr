import os
import atexit
import json
import ast
import time
from peewee import Model, AutoField, TextField, IntegerField, ForeignKeyField, BlobField, BooleanField
from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.migrate import SqliteMigrator, migrate
from playhouse.sqlite_ext import RowIDField

from helper import path_mappings
from config import settings, get_array_from
from get_args import args

database = SqliteQueueDatabase(os.path.join(args.config_dir, 'db', 'bazarr.db'),
                               use_gevent=False,
                               autostart=True,
                               queue_max_size=256)
migrator = SqliteMigrator(database)


@atexit.register
def _stop_worker_threads():
    database.stop()


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


class TableBlacklist(BaseModel):
    language = TextField(null=True)
    provider = TextField(null=True)
    sonarr_episode_id = IntegerField(null=True)
    sonarr_series_id = IntegerField(null=True)
    subs_id = TextField(null=True)
    timestamp = IntegerField(null=True)

    class Meta:
        table_name = 'table_blacklist'
        primary_key = False


class TableBlacklistMovie(BaseModel):
    language = TextField(null=True)
    provider = TextField(null=True)
    radarr_id = IntegerField(null=True)
    subs_id = TextField(null=True)
    timestamp = IntegerField(null=True)

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
    file_size = IntegerField(default=0, null=True)
    format = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    path = TextField()
    resolution = TextField(null=True)
    scene_name = TextField(null=True)
    season = IntegerField()
    sonarrEpisodeId = IntegerField(unique=True)
    sonarrSeriesId = IntegerField()
    subtitles = TextField(null=True)
    title = TextField()
    video_codec = TextField(null=True)

    class Meta:
        table_name = 'table_episodes'
        primary_key = False


class TableHistory(BaseModel):
    action = IntegerField()
    description = TextField()
    id = AutoField()
    language = TextField(null=True)
    provider = TextField(null=True)
    score = TextField(null=True)
    sonarrEpisodeId = IntegerField()
    sonarrSeriesId = IntegerField()
    subs_id = TextField(null=True)
    subtitles_path = TextField(null=True)
    timestamp = IntegerField()
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
    score = TextField(null=True)
    subs_id = TextField(null=True)
    subtitles_path = TextField(null=True)
    timestamp = IntegerField()
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history_movie'


class TableLanguagesProfiles(BaseModel):
    cutoff = IntegerField(null=True)
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
    file_size = IntegerField(default=0, null=True)
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
    alternateTitles = TextField(null=True)
    audio_language = TextField(null=True)
    fanart = TextField(null=True)
    imdbId = TextField(default='""', null=True)
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
                            TableCustomScoreProfileConditions])

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
    migrate(
        migrator.add_column('table_shows', 'year', TextField(null=True)),
        migrator.add_column('table_shows', 'alternateTitles', TextField(null=True)),
        migrator.add_column('table_shows', 'tags', TextField(default='[]', null=True)),
        migrator.add_column('table_shows', 'seriesType', TextField(default='""', null=True)),
        migrator.add_column('table_shows', 'imdbId', TextField(default='""', null=True)),
        migrator.add_column('table_shows', 'profileId', IntegerField(null=True)),
        migrator.add_column('table_episodes', 'format', TextField(null=True)),
        migrator.add_column('table_episodes', 'resolution', TextField(null=True)),
        migrator.add_column('table_episodes', 'video_codec', TextField(null=True)),
        migrator.add_column('table_episodes', 'audio_codec', TextField(null=True)),
        migrator.add_column('table_episodes', 'episode_file_id', IntegerField(null=True)),
        migrator.add_column('table_episodes', 'audio_language', TextField(null=True)),
        migrator.add_column('table_episodes', 'file_size', IntegerField(default=0, null=True)),
        migrator.add_column('table_episodes', 'ffprobe_cache', BlobField(null=True)),
        migrator.add_column('table_movies', 'sortTitle', TextField(null=True)),
        migrator.add_column('table_movies', 'year', TextField(null=True)),
        migrator.add_column('table_movies', 'alternativeTitles', TextField(null=True)),
        migrator.add_column('table_movies', 'format', TextField(null=True)),
        migrator.add_column('table_movies', 'resolution', TextField(null=True)),
        migrator.add_column('table_movies', 'video_codec', TextField(null=True)),
        migrator.add_column('table_movies', 'audio_codec', TextField(null=True)),
        migrator.add_column('table_movies', 'imdbId', TextField(null=True)),
        migrator.add_column('table_movies', 'movie_file_id', IntegerField(null=True)),
        migrator.add_column('table_movies', 'tags', TextField(default='[]', null=True)),
        migrator.add_column('table_movies', 'profileId', IntegerField(null=True)),
        migrator.add_column('table_movies', 'file_size', IntegerField(default=0, null=True)),
        migrator.add_column('table_movies', 'ffprobe_cache', BlobField(null=True)),
        migrator.add_column('table_history', 'video_path', TextField(null=True)),
        migrator.add_column('table_history', 'language', TextField(null=True)),
        migrator.add_column('table_history', 'provider', TextField(null=True)),
        migrator.add_column('table_history', 'score', TextField(null=True)),
        migrator.add_column('table_history', 'subs_id', TextField(null=True)),
        migrator.add_column('table_history', 'subtitles_path', TextField(null=True)),
        migrator.add_column('table_history_movie', 'video_path', TextField(null=True)),
        migrator.add_column('table_history_movie', 'language', TextField(null=True)),
        migrator.add_column('table_history_movie', 'provider', TextField(null=True)),
        migrator.add_column('table_history_movie', 'score', TextField(null=True)),
        migrator.add_column('table_history_movie', 'subs_id', TextField(null=True)),
        migrator.add_column('table_history_movie', 'subtitles_path', TextField(null=True)),
        migrator.add_column('table_languages_profiles', 'mustContain', TextField(null=True)),
        migrator.add_column('table_languages_profiles', 'mustNotContain', TextField(null=True)),
    )


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
            where_clause.append(~(TableShows.tags.contains("\'"+tag+"\'")))
    else:
        tagsList = ast.literal_eval(settings.radarr.excluded_tags)
        for tag in tagsList:
            where_clause.append(~(TableMovies.tags.contains("\'"+tag+"\'")))

    if exclusion_type == 'series':
        monitoredOnly = settings.sonarr.getboolean('only_monitored')
        if monitoredOnly:
            where_clause.append((TableEpisodes.monitored == 'True'))
    else:
        monitoredOnly = settings.radarr.getboolean('only_monitored')
        if monitoredOnly:
            where_clause.append((TableMovies.monitored == 'True'))

    if exclusion_type == 'series':
        typesList = get_array_from(settings.sonarr.excluded_series_types)
        for item in typesList:
            where_clause.append((TableShows.seriesType != item))

        exclude_season_zero = settings.sonarr.getboolean('exclude_season_zero')
        if exclude_season_zero:
            where_clause.append((TableEpisodes.season != 0))

    return where_clause


def update_profile_id_list():
    global profile_id_list
    profile_id_list = TableLanguagesProfiles.select(TableLanguagesProfiles.profileId,
                                                    TableLanguagesProfiles.name,
                                                    TableLanguagesProfiles.cutoff,
                                                    TableLanguagesProfiles.items,
                                                    TableLanguagesProfiles.mustContain,
                                                    TableLanguagesProfiles.mustNotContain).dicts()
    profile_id_list = list(profile_id_list)
    for profile in profile_id_list:
        profile['items'] = json.loads(profile['items'])
        profile['mustContain'] = ast.literal_eval(profile['mustContain']) if profile['mustContain'] else \
            profile['mustContain']
        profile['mustNotContain'] = ast.literal_eval(profile['mustNotContain']) if profile['mustNotContain'] else \
            profile['mustNotContain']


def get_profiles_list(profile_id=None):
    try:
        len(profile_id_list)
    except NameError:
        update_profile_id_list()

    if profile_id and profile_id != 'null':
        for profile in profile_id_list:
            if profile['profileId'] == profile_id:
                return profile
    else:
        return profile_id_list


def get_desired_languages(profile_id):
    languages = []

    if not len(profile_id_list):
        update_profile_id_list()

    if profile_id and profile_id != 'null':
        for profile in profile_id_list:
            profileId, name, cutoff, items, mustContain, mustNotContain = profile.values()
            if profileId == int(profile_id):
                languages = [x['language'] for x in items]
                break

    return languages


def get_profile_id_name(profile_id):
    name_from_id = None

    if not len(profile_id_list):
        update_profile_id_list()

    if profile_id and profile_id != 'null':
        for profile in profile_id_list:
            profileId, name, cutoff, items, mustContain, mustNotContain = profile.values()
            if profileId == int(profile_id):
                name_from_id = name
                break

    return name_from_id


def get_profile_cutoff(profile_id):
    cutoff_language = None

    if not len(profile_id_list):
        update_profile_id_list()

    if profile_id and profile_id != 'null':
        cutoff_language = []
        for profile in profile_id_list:
            profileId, name, cutoff, items, mustContain, mustNotContain = profile.values()
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


def get_audio_profile_languages(series_id=None, episode_id=None, movie_id=None):
    from get_languages import alpha2_from_language, alpha3_from_language
    audio_languages = []

    if series_id:
        audio_languages_list_str = TableShows.get(TableShows.sonarrSeriesId == series_id).audio_language
    elif episode_id:
        audio_languages_list_str = TableEpisodes.get(TableEpisodes.sonarrEpisodeId == episode_id).audio_language
    elif movie_id:
        audio_languages_list_str = TableMovies.get(TableMovies.radarrId == movie_id).audio_language
    else:
        return audio_languages

    try:
        audio_languages_list = ast.literal_eval(audio_languages_list_str)
    except ValueError:
        pass
    else:
        for language in audio_languages_list:
            audio_languages.append(
                {"name": language,
                 "code2": alpha2_from_language(language) or None,
                 "code3": alpha3_from_language(language) or None}
            )

    return audio_languages


def get_profile_id(series_id=None, episode_id=None, movie_id=None):
    if series_id:
        profileId = TableShows.get(TableShows.sonarrSeriesId == series_id).profileId
    elif episode_id:
        profileId = TableShows.select(TableShows.profileId)\
            .join(TableEpisodes, on=(TableShows.sonarrSeriesId == TableEpisodes.sonarrSeriesId))\
            .where(TableEpisodes.sonarrEpisodeId == episode_id)\
            .get().profileId
    elif movie_id:
        profileId = TableMovies.get(TableMovies.radarrId == movie_id).profileId
    else:
        return None

    return profileId


def convert_list_to_clause(arr: list):
    if isinstance(arr, list):
        return f"({','.join(str(x) for x in arr)})"
    else:
        return ""
