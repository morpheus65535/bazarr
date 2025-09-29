# -*- coding: utf-8 -*-
import ast
import atexit
import json
import logging
import os
import flask_migrate
import signal

from dogpile.cache import make_region
from datetime import datetime

from sqlalchemy import create_engine, inspect, DateTime, ForeignKey, Integer, LargeBinary, Text, func, text, BigInteger
# importing here to be indirectly imported in other modules later
from sqlalchemy import update, delete, select, func  # noqa W0611
from sqlalchemy.orm import scoped_session, sessionmaker, mapped_column, close_all_sessions
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool

from flask_sqlalchemy import SQLAlchemy

from .config import settings
from .get_args import args

logger = logging.getLogger(__name__)

POSTGRES_ENABLED_ENV = os.getenv("POSTGRES_ENABLED")
if POSTGRES_ENABLED_ENV:
    postgresql = POSTGRES_ENABLED_ENV.lower() == 'true'
else:
    postgresql = settings.postgresql.enabled

region = make_region().configure('dogpile.cache.memory')

migrations_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'migrations')

if postgresql:
    # insert is different between database types
    from sqlalchemy.dialects.postgresql import insert  # noqa E402
    from sqlalchemy.engine import URL, make_url  # noqa E402

    postgres_database = os.getenv("POSTGRES_DATABASE", settings.postgresql.database)
    postgres_username = os.getenv("POSTGRES_USERNAME", settings.postgresql.username)
    postgres_password = os.getenv("POSTGRES_PASSWORD", settings.postgresql.password)
    postgres_host = os.getenv("POSTGRES_HOST", settings.postgresql.host)
    postgres_port = os.getenv("POSTGRES_PORT", settings.postgresql.port)
    postgres_url = os.getenv("POSTGRES_URL", settings.postgresql.url)

    if postgres_url:
        url = make_url(postgres_url)
        backend_name = url.get_backend_name()
        if backend_name != 'postgresql':
            raise ValueError(f"Invalid Postgres URL, scheme must be 'postgresql', got {backend_name}")
        
        # Allow overriding individual components of the URL
        url_overrides = {
            'username': postgres_username if postgres_username else None,
            'password': postgres_password if postgres_password else None,
            'host': postgres_host if postgres_host else None,
            'port': postgres_port if postgres_port else None,
            'database': postgres_database if postgres_database else None,
        }
        url = url.set(**{k: v for k, v in url_overrides.items()})
    else:
        url = URL.create(
            drivername="postgresql",
            username=postgres_username,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port,
            database=postgres_database
        )
    logger.debug(f"Connecting to PostgreSQL database: {url.render_as_string(hide_password=True)}")
    
    engine = create_engine(url, poolclass=NullPool, isolation_level="AUTOCOMMIT")
else:
    # insert is different between database types
    from sqlalchemy.dialects.sqlite import insert  # noqa E402
    url = f'sqlite:///{os.path.join(args.config_dir, "db", "bazarr.db")}'
    logger.debug(f"Connecting to SQLite database: {url}")
    engine = create_engine(url, poolclass=NullPool, isolation_level="AUTOCOMMIT")

    from sqlalchemy.engine import Engine
    from sqlalchemy import event

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

session_factory = sessionmaker(bind=engine)
database = scoped_session(session_factory)


def close_database():
    close_all_sessions()
    engine.dispose()


@atexit.register
def _stop_worker_threads():
    database.remove()


signal.signal(signal.SIGTERM, lambda signal_no, frame: close_database())

Base = declarative_base()
metadata = Base.metadata


class System(Base):
    __tablename__ = 'system'

    id = mapped_column(Integer, primary_key=True)
    configured = mapped_column(Text)
    updated = mapped_column(Text)


class TableAnnouncements(Base):
    __tablename__ = 'table_announcements'

    id = mapped_column(Integer, primary_key=True)
    timestamp = mapped_column(DateTime, nullable=False, default=datetime.now)
    hash = mapped_column(Text)
    text = mapped_column(Text)


class TableBlacklist(Base):
    __tablename__ = 'table_blacklist'

    id = mapped_column(Integer, primary_key=True)
    language = mapped_column(Text)
    provider = mapped_column(Text)
    sonarr_episode_id = mapped_column(Integer, ForeignKey('table_episodes.sonarrEpisodeId', ondelete='CASCADE'))
    sonarr_series_id = mapped_column(Integer, ForeignKey('table_shows.sonarrSeriesId', ondelete='CASCADE'))
    subs_id = mapped_column(Text)
    timestamp = mapped_column(DateTime, default=datetime.now)


class TableBlacklistMovie(Base):
    __tablename__ = 'table_blacklist_movie'

    id = mapped_column(Integer, primary_key=True)
    language = mapped_column(Text)
    provider = mapped_column(Text)
    radarr_id = mapped_column(Integer, ForeignKey('table_movies.radarrId', ondelete='CASCADE'))
    subs_id = mapped_column(Text)
    timestamp = mapped_column(DateTime, default=datetime.now)


class TableEpisodes(Base):
    __tablename__ = 'table_episodes'

    audio_codec = mapped_column(Text)
    audio_language = mapped_column(Text)
    created_at_timestamp = mapped_column(DateTime)
    episode = mapped_column(Integer, nullable=False)
    episode_file_id = mapped_column(Integer)
    failedAttempts = mapped_column(Text)
    ffprobe_cache = mapped_column(LargeBinary)
    file_size = mapped_column(BigInteger)
    format = mapped_column(Text)
    missing_subtitles = mapped_column(Text)
    monitored = mapped_column(Text)
    path = mapped_column(Text, nullable=False)
    resolution = mapped_column(Text)
    sceneName = mapped_column(Text)
    season = mapped_column(Integer, nullable=False)
    sonarrEpisodeId = mapped_column(Integer, primary_key=True)
    sonarrSeriesId = mapped_column(Integer, ForeignKey('table_shows.sonarrSeriesId', ondelete='CASCADE'))
    subtitles = mapped_column(Text)
    title = mapped_column(Text, nullable=False)
    updated_at_timestamp = mapped_column(DateTime)
    video_codec = mapped_column(Text)


class TableHistory(Base):
    __tablename__ = 'table_history'

    id = mapped_column(Integer, primary_key=True)
    action = mapped_column(Integer, nullable=False)
    description = mapped_column(Text, nullable=False)
    language = mapped_column(Text)
    provider = mapped_column(Text)
    score = mapped_column(Integer)
    sonarrEpisodeId = mapped_column(Integer, ForeignKey('table_episodes.sonarrEpisodeId', ondelete='CASCADE'))
    sonarrSeriesId = mapped_column(Integer, ForeignKey('table_shows.sonarrSeriesId', ondelete='CASCADE'))
    subs_id = mapped_column(Text)
    subtitles_path = mapped_column(Text)
    timestamp = mapped_column(DateTime, nullable=False, default=datetime.now)
    video_path = mapped_column(Text)
    matched = mapped_column(Text)
    not_matched = mapped_column(Text)
    upgradedFromId = mapped_column(Integer, ForeignKey('table_history.id'))


class TableHistoryMovie(Base):
    __tablename__ = 'table_history_movie'

    id = mapped_column(Integer, primary_key=True)
    action = mapped_column(Integer, nullable=False)
    description = mapped_column(Text, nullable=False)
    language = mapped_column(Text)
    provider = mapped_column(Text)
    radarrId = mapped_column(Integer, ForeignKey('table_movies.radarrId', ondelete='CASCADE'))
    score = mapped_column(Integer)
    subs_id = mapped_column(Text)
    subtitles_path = mapped_column(Text)
    timestamp = mapped_column(DateTime, nullable=False, default=datetime.now)
    video_path = mapped_column(Text)
    matched = mapped_column(Text)
    not_matched = mapped_column(Text)
    upgradedFromId = mapped_column(Integer, ForeignKey('table_history_movie.id'))


class TableLanguagesProfiles(Base):
    __tablename__ = 'table_languages_profiles'

    profileId = mapped_column(Integer, primary_key=True)
    cutoff = mapped_column(Integer)
    originalFormat = mapped_column(Integer)
    items = mapped_column(Text, nullable=False)
    name = mapped_column(Text, nullable=False)
    mustContain = mapped_column(Text)
    mustNotContain = mapped_column(Text)
    tag = mapped_column(Text)


class TableMovies(Base):
    __tablename__ = 'table_movies'

    alternativeTitles = mapped_column(Text)
    audio_codec = mapped_column(Text)
    audio_language = mapped_column(Text)
    created_at_timestamp = mapped_column(DateTime)
    failedAttempts = mapped_column(Text)
    fanart = mapped_column(Text)
    ffprobe_cache = mapped_column(LargeBinary)
    file_size = mapped_column(BigInteger)
    format = mapped_column(Text)
    imdbId = mapped_column(Text)
    missing_subtitles = mapped_column(Text)
    monitored = mapped_column(Text)
    movie_file_id = mapped_column(Integer)
    overview = mapped_column(Text)
    path = mapped_column(Text, nullable=False, unique=True)
    poster = mapped_column(Text)
    profileId = mapped_column(Integer, ForeignKey('table_languages_profiles.profileId', ondelete='SET NULL'))
    radarrId = mapped_column(Integer, primary_key=True)
    resolution = mapped_column(Text)
    sceneName = mapped_column(Text)
    sortTitle = mapped_column(Text)
    subtitles = mapped_column(Text)
    tags = mapped_column(Text)
    title = mapped_column(Text, nullable=False)
    tmdbId = mapped_column(Text, nullable=False, unique=True)
    updated_at_timestamp = mapped_column(DateTime)
    video_codec = mapped_column(Text)
    year = mapped_column(Text)


class TableMoviesRootfolder(Base):
    __tablename__ = 'table_movies_rootfolder'

    accessible = mapped_column(Integer)
    error = mapped_column(Text)
    id = mapped_column(Integer, primary_key=True)
    path = mapped_column(Text)


class TableSettingsLanguages(Base):
    __tablename__ = 'table_settings_languages'

    code3 = mapped_column(Text, primary_key=True)
    code2 = mapped_column(Text)
    code3b = mapped_column(Text)
    enabled = mapped_column(Integer)
    name = mapped_column(Text, nullable=False)


class TableSettingsNotifier(Base):
    __tablename__ = 'table_settings_notifier'

    name = mapped_column(Text, primary_key=True)
    enabled = mapped_column(Integer)
    url = mapped_column(Text)


class TableShows(Base):
    __tablename__ = 'table_shows'

    tvdbId = mapped_column(Integer)
    alternativeTitles = mapped_column(Text)
    audio_language = mapped_column(Text)
    created_at_timestamp = mapped_column(DateTime)
    ended = mapped_column(Text)
    fanart = mapped_column(Text)
    imdbId = mapped_column(Text)
    lastAired = mapped_column(Text)
    monitored = mapped_column(Text)
    overview = mapped_column(Text)
    path = mapped_column(Text, nullable=False, unique=True)
    poster = mapped_column(Text)
    profileId = mapped_column(Integer, ForeignKey('table_languages_profiles.profileId', ondelete='SET NULL'))
    seriesType = mapped_column(Text)
    sonarrSeriesId = mapped_column(Integer, primary_key=True)
    sortTitle = mapped_column(Text)
    tags = mapped_column(Text)
    title = mapped_column(Text, nullable=False)
    updated_at_timestamp = mapped_column(DateTime)
    year = mapped_column(Text)


class TableShowsRootfolder(Base):
    __tablename__ = 'table_shows_rootfolder'

    accessible = mapped_column(Integer)
    error = mapped_column(Text)
    id = mapped_column(Integer, primary_key=True)
    path = mapped_column(Text)


def init_db():
    database.begin()

    # Create tables if they don't exist.
    metadata.create_all(engine)


def create_db_revision(app):
    logging.info("Creating a new database revision for future migration")
    app.config["SQLALCHEMY_DATABASE_URI"] = url
    db = SQLAlchemy(app, metadata=metadata)
    with app.app_context():
        flask_migrate.Migrate(app, db, render_as_batch=True)
        flask_migrate.migrate(directory=migrations_directory)
        db.engine.dispose()


def migrate_db(app):
    logging.debug("Upgrading database schema")
    app.config["SQLALCHEMY_DATABASE_URI"] = url
    db = SQLAlchemy(app, metadata=metadata)

    insp = inspect(engine)
    alembic_temp_tables_list = [x for x in insp.get_table_names() if x.startswith('_alembic_tmp_')]
    for table in alembic_temp_tables_list:
        database.execute(text(f"DROP TABLE IF EXISTS {table}"))

    with app.app_context():
        flask_migrate.Migrate(app, db, render_as_batch=True)
        flask_migrate.upgrade(directory=migrations_directory)
        db.engine.dispose()

    # add the system table single row if it's not existing
    if not database.execute(
            select(System)) \
            .first():
        database.execute(
            insert(System)
            .values(configured='0', updated='0'))


def get_exclusion_clause(exclusion_type):
    where_clause = []
    if exclusion_type == 'series':
        tagsList = settings.sonarr.excluded_tags
        for tag in tagsList:
            where_clause.append(~(TableShows.tags.contains(f"\'{tag}\'")))
    else:
        tagsList = settings.radarr.excluded_tags
        for tag in tagsList:
            where_clause.append(~(TableMovies.tags.contains(f"\'{tag}\'")))

    if exclusion_type == 'series':
        monitoredOnly = settings.sonarr.only_monitored
        if monitoredOnly:
            where_clause.append((TableEpisodes.monitored == 'True'))  # noqa E712
            where_clause.append((TableShows.monitored == 'True'))  # noqa E712
    else:
        monitoredOnly = settings.radarr.only_monitored
        if monitoredOnly:
            where_clause.append((TableMovies.monitored == 'True'))  # noqa E712

    if exclusion_type == 'series':
        typesList = settings.sonarr.excluded_series_types
        for item in typesList:
            where_clause.append((TableShows.seriesType != item))

        exclude_season_zero = settings.sonarr.exclude_season_zero
        if exclude_season_zero:
            where_clause.append((TableEpisodes.season != 0))

    return where_clause


@region.cache_on_arguments()
def update_profile_id_list():
    return [{
        'profileId': x.profileId,
        'name': x.name,
        'cutoff': x.cutoff,
        'items': json.loads(x.items),
        'mustContain': ast.literal_eval(x.mustContain) if x.mustContain else [],
        'mustNotContain': ast.literal_eval(x.mustNotContain) if x.mustNotContain else [],
        'originalFormat': x.originalFormat,
        'tag': x.tag,
    } for x in database.execute(
        select(TableLanguagesProfiles.profileId,
               TableLanguagesProfiles.name,
               TableLanguagesProfiles.cutoff,
               TableLanguagesProfiles.items,
               TableLanguagesProfiles.mustContain,
               TableLanguagesProfiles.mustNotContain,
               TableLanguagesProfiles.originalFormat,
               TableLanguagesProfiles.tag))
        .all()
    ]


def get_profiles_list(profile_id=None):
    profile_id_list = update_profile_id_list()

    if profile_id and profile_id != 'null':
        for profile in profile_id_list:
            if profile['profileId'] == profile_id:
                return profile
    else:
        return profile_id_list


def get_desired_languages(profile_id):
    for profile in update_profile_id_list():
        if profile['profileId'] == profile_id:
            return [x['language'] for x in profile['items']]


def get_profile_id_name(profile_id):
    for profile in update_profile_id_list():
        if profile['profileId'] == profile_id:
            return profile['name']


def get_profile_cutoff(profile_id):
    cutoff_language = None
    profile_id_list = update_profile_id_list()

    if profile_id and profile_id != 'null':
        cutoff_language = []
        for profile in profile_id_list:
            profileId, name, cutoff, items, mustContain, mustNotContain, originalFormat, tag = profile.values()
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
        data = database.execute(
            select(TableShows.profileId)
            .where(TableShows.sonarrSeriesId == series_id))\
            .first()
        if data:
            return data.profileId
    elif episode_id:
        data = database.execute(
            select(TableShows.profileId)
            .select_from(TableShows)
            .join(TableEpisodes)
            .where(TableEpisodes.sonarrEpisodeId == episode_id)) \
            .first()
        if data:
            return data.profileId

    elif movie_id:
        data = database.execute(
            select(TableMovies.profileId)
            .where(TableMovies.radarrId == movie_id))\
            .first()
        if data:
            return data.profileId

    return None


def convert_list_to_clause(arr: list):
    if isinstance(arr, list):
        return f"({','.join(str(x) for x in arr)})"
    else:
        return ""


def upgrade_languages_profile_values():
    for languages_profile in (database.execute(
            select(
                TableLanguagesProfiles.profileId,
                TableLanguagesProfiles.name,
                TableLanguagesProfiles.cutoff,
                TableLanguagesProfiles.items,
                TableLanguagesProfiles.mustContain,
                TableLanguagesProfiles.mustNotContain,
                TableLanguagesProfiles.originalFormat,
                TableLanguagesProfiles.tag)
            ))\
            .all():
        items = json.loads(languages_profile.items)
        for language in items:
            if language['hi'] == "only":
                language['hi'] = "True"
            elif language['hi'] in ["also", "never"]:
                language['hi'] = "False"

            if 'audio_only_include' not in language:
                language['audio_only_include'] = "False"
        database.execute(
            update(TableLanguagesProfiles)
            .values({"items": json.dumps(items)})
            .where(TableLanguagesProfiles.profileId == languages_profile.profileId)
        )


def fix_languages_profiles_with_duplicate_ids():
    languages_profiles = database.execute(
        select(TableLanguagesProfiles.profileId, TableLanguagesProfiles.items, TableLanguagesProfiles.cutoff)).all()
    for languages_profile in languages_profiles:
        if languages_profile.cutoff:
            # ignore profiles that have a cutoff set
            continue
        languages_profile_ids = []
        languages_profile_has_duplicate = False
        languages_profile_items = json.loads(languages_profile.items)
        for items in languages_profile_items:
            if items['id'] in languages_profile_ids:
                languages_profile_has_duplicate = True
                break
            else:
                languages_profile_ids.append(items['id'])

        if languages_profile_has_duplicate:
            item_id = 0
            for items in languages_profile_items:
                item_id += 1
                items['id'] = item_id
            database.execute(
                update(TableLanguagesProfiles)
                .values({"items": json.dumps(languages_profile_items)})
                .where(TableLanguagesProfiles.profileId == languages_profile.profileId)
            )
