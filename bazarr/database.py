import os
import atexit
import json
import ast
import gevent
from peewee import Model, TextField, IntegerField, ForeignKeyField, BlobField, BooleanField
from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.sqlite_ext import AutoIncrementField
from playhouse.migrate import SqliteMigrator

from config import settings, get_array_from
from get_args import args

database = SqliteQueueDatabase(os.path.join(args.config_dir, 'db', 'bazarr.db'),
                               use_gevent=True,
                               autostart=True,
                               queue_max_size=256)
database.pragma('foreign_keys', 'on')  # Enable foreign keys enforcement
database.pragma('wal_checkpoint', 'TRUNCATE')  # Run a checkpoint and merge remaining wal-journal.
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


class TableLanguagesProfiles(BaseModel):
    cutoff = IntegerField(null=True)
    items = TextField(null=False)
    name = TextField(null=False)
    profileId = AutoIncrementField()

    class Meta:
        table_name = 'table_languages_profiles'


class TableShowsRootfolder(BaseModel):
    accessible = IntegerField(null=True)
    error = TextField(null=True)
    rootId = AutoIncrementField()
    path = TextField(null=False)

    class Meta:
        table_name = 'table_shows_rootfolder'


class TableShows(BaseModel):
    alternateTitles = TextField(null=True)
    fanart = TextField(null=True)
    imdbId = TextField(null=True)
    overview = TextField(null=True)
    path = TextField(unique=True, null=False)
    poster = TextField(null=True)
    profileId = ForeignKeyField(TableLanguagesProfiles, db_column="profileId", null=True, on_delete='CASCADE')
    seriesType = TextField(null=True)
    seriesId = AutoIncrementField()
    sortTitle = TextField(null=True)
    tags = TextField(null=True)
    title = TextField(null=False)
    tmdbId = TextField(unique=True, null=False)
    year = TextField(null=True)
    rootdir = ForeignKeyField(TableShowsRootfolder, db_column="rootId", on_delete='CASCADE')

    class Meta:
        table_name = 'table_shows'


class TableEpisodes(BaseModel):
    audio_codec = TextField(null=True)
    audio_language = TextField(null=True)
    episode = IntegerField(null=False)
    failedAttempts = TextField(null=True)
    ffprobe_cache = BlobField(null=True)
    file_size = IntegerField(default=0, null=True)
    format = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    path = TextField(null=False)
    resolution = TextField(null=True)
    season = IntegerField(null=False)
    episodeId = AutoIncrementField()
    seriesId = ForeignKeyField(TableShows, db_column="seriesId", on_delete='CASCADE')
    subtitles = TextField(null=True)
    title = TextField(null=False)
    video_codec = TextField(null=True)

    class Meta:
        table_name = 'table_episodes'


class TableHistory(BaseModel):
    action = IntegerField(null=False)
    description = TextField(null=False)
    id = AutoIncrementField()
    language = TextField(null=True)
    provider = TextField(null=True)
    score = TextField(null=True)
    episodeId = ForeignKeyField(TableEpisodes, db_column="episodeId", on_delete='CASCADE')
    seriesId = ForeignKeyField(TableShows, db_column="seriesId", on_delete='CASCADE')
    subs_id = TextField(null=True)
    subtitles_path = TextField(null=True)
    timestamp = IntegerField(null=False)
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history'


class TableBlacklist(BaseModel):
    language = TextField(null=False)
    provider = TextField(null=False)
    episode_id = ForeignKeyField(TableEpisodes, db_column="episodeId", on_delete='CASCADE')
    series_id = ForeignKeyField(TableShows, db_column="seriesId", on_delete='CASCADE')
    subs_id = TextField(null=False)
    timestamp = IntegerField(null=False)

    class Meta:
        table_name = 'table_blacklist'


class TableMoviesRootfolder(BaseModel):
    accessible = IntegerField(null=True)
    error = TextField(null=True)
    rootId = AutoIncrementField()
    path = TextField(null=False)

    class Meta:
        table_name = 'table_movies_rootfolder'


class TableMovies(BaseModel):
    alternativeTitles = TextField(null=True)
    audio_codec = TextField(null=True)
    audio_language = TextField(null=True)
    failedAttempts = TextField(null=True)
    fanart = TextField(null=True)
    ffprobe_cache = BlobField(null=True)
    file_size = IntegerField(default=0, null=False)
    format = TextField(null=True)
    imdbId = TextField(null=True)
    missing_subtitles = TextField(null=True)
    monitored = TextField(null=True)
    overview = TextField(null=True)
    path = TextField(unique=True, null=False)
    poster = TextField(null=True)
    profileId = ForeignKeyField(TableLanguagesProfiles, db_column="profileId", null=True, on_delete='CASCADE')
    movieId = AutoIncrementField()
    resolution = TextField(null=True)
    sortTitle = TextField(null=True)
    subtitles = TextField(null=True)
    tags = TextField(null=True)
    title = TextField(null=False)
    tmdbId = TextField(unique=True, null=False)
    video_codec = TextField(null=True)
    year = TextField(null=True)
    rootdir = ForeignKeyField(TableMoviesRootfolder, db_column="rootId", on_delete='CASCADE')

    class Meta:
        table_name = 'table_movies'


class TableHistoryMovie(BaseModel):
    action = IntegerField(null=False)
    description = TextField(null=False)
    id = AutoIncrementField()
    language = TextField(null=True)
    provider = TextField(null=True)
    movieId = ForeignKeyField(TableMovies, db_column="movieId", on_delete='CASCADE')
    score = TextField(null=True)
    subs_id = TextField(null=True)
    subtitles_path = TextField(null=True)
    timestamp = IntegerField(null=False)
    video_path = TextField(null=True)

    class Meta:
        table_name = 'table_history_movie'


class TableBlacklistMovie(BaseModel):
    language = TextField(null=False)
    provider = TextField(null=False)
    movie_id = ForeignKeyField(TableMovies, db_column="movieId", on_delete='CASCADE')
    subs_id = TextField(null=False)
    timestamp = IntegerField(null=False)

    class Meta:
        table_name = 'table_blacklist_movie'


class TableSettingsLanguages(BaseModel):
    code2 = TextField(null=False)
    code3 = TextField(primary_key=True, null=False)
    code3b = TextField(null=True)
    enabled = IntegerField(null=True)
    name = TextField(null=False)

    class Meta:
        table_name = 'table_settings_languages'


class TableSettingsNotifier(BaseModel):
    enabled = IntegerField(null=True)
    name = TextField(null=True, primary_key=True)
    url = TextField(null=True)

    class Meta:
        table_name = 'table_settings_notifier'


class TableCustomScoreProfiles(BaseModel):
    id = AutoIncrementField()
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


class TableTmdbCache(BaseModel):
    id = AutoIncrementField()
    timestamp = IntegerField(null=False)
    function = BlobField(null=False)
    arguments = BlobField(null=True)
    result = BlobField(null=False)

    class Meta:
        table_name = 'table_tmdb_cache'


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
                            TableTmdbCache])

    # add the system table single row if it's not existing
    # we must retry until the tables are created
    tables_created = False
    while not tables_created:
        try:
            if not System.select().count():
                System.insert({System.configured: '0', System.updated: '0'}).execute()
        except Exception:
            gevent.sleep(0.1)
        else:
            tables_created = True


def migrate_db():
    pass
    # migrate(
    #     migrator.add_column('table_shows', 'year', TextField(null=True))
    # )


def get_exclusion_clause(exclusion_type):
    where_clause = []
    if exclusion_type == 'series':
        tagsList = ast.literal_eval(settings.series.excluded_tags)
        for tag in tagsList:
            where_clause.append(~(TableShows.tags.contains("\'"+tag+"\'")))
    else:
        tagsList = ast.literal_eval(settings.movies.excluded_tags)
        for tag in tagsList:
            where_clause.append(~(TableMovies.tags.contains("\'"+tag+"\'")))

    if exclusion_type == 'series':
        monitoredOnly = settings.series.getboolean('only_monitored')
        if monitoredOnly:
            where_clause.append((TableEpisodes.monitored == 'True'))
    else:
        monitoredOnly = settings.movies.getboolean('only_monitored')
        if monitoredOnly:
            where_clause.append((TableMovies.monitored == 'True'))

    if exclusion_type == 'series':
        typesList = get_array_from(settings.series.excluded_series_types)
        for item in typesList:
            where_clause.append((TableShows.seriesType != item))

    return where_clause


def update_profile_id_list():
    global profile_id_list
    profile_id_list = TableLanguagesProfiles.select(TableLanguagesProfiles.profileId,
                                                    TableLanguagesProfiles.name,
                                                    TableLanguagesProfiles.cutoff,
                                                    TableLanguagesProfiles.items).dicts()
    profile_id_list = list(profile_id_list)
    for profile in profile_id_list:
        profile['items'] = json.loads(profile['items'])


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
            profileId, name, cutoff, items = profile.values()
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
            profileId, name, cutoff, items = profile.values()
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
            profileId, name, cutoff, items = profile.values()
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
        audio_languages_list_str = TableShows.get(TableShows.seriesId == series_id).audio_language
    elif episode_id:
        audio_languages_list_str = TableEpisodes.get(TableEpisodes.episodeId == episode_id).audio_language
    elif movie_id:
        audio_languages_list_str = TableMovies.get(TableMovies.movieId == movie_id).audio_language
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


def convert_list_to_clause(arr: list):
    if isinstance(arr, list):
        return f"({','.join(str(x) for x in arr)})"
    else:
        return ""
