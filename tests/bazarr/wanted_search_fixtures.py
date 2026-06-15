import importlib
from itertools import count
from types import SimpleNamespace

import pytest
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

_metadata = MetaData()
_movie_rows = Table(
    "table_movies",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("path", String, nullable=True),
    Column("missing_subtitles", String, nullable=True),
    Column("radarrId", Integer, nullable=False),
    Column("audio_language", String, nullable=False),
    Column("sceneName", String, nullable=True),
    Column("failedAttempts", String, nullable=False),
    Column("title", String, nullable=False),
    Column("year", Integer, nullable=False),
    Column("imdbId", String, nullable=True),
    Column("tmdbId", Integer, nullable=True),
    Column("profileId", Integer, nullable=False),
    Column("tags", String, nullable=False),
    Column("monitored", Boolean, nullable=False),
    Column("has_indexed_subtitles", Boolean, nullable=False),
    Column("has_incomplete_embedded_subtitles", Boolean, nullable=False),
)
_episode_rows = Table(
    "table_episodes",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("path", String, nullable=True),
    Column("missing_subtitles", String, nullable=True),
    Column("sonarrEpisodeId", Integer, nullable=False),
    Column("sonarrSeriesId", Integer, ForeignKey("table_shows.sonarrSeriesId"), nullable=False),
    Column("audio_language", String, nullable=False),
    Column("sceneName", String, nullable=True),
    Column("failedAttempts", String, nullable=False),
    Column("title", String, nullable=False),
    Column("profileId", Integer, nullable=False),
    Column("season", Integer, nullable=True),
    Column("episode", Integer, nullable=True),
    Column("episodeTitle", String, nullable=False),
    Column("monitored", Boolean, nullable=False),
    Column("has_indexed_subtitles", Boolean, nullable=False),
    Column("has_incomplete_embedded_subtitles", Boolean, nullable=False),
)
_show_rows = Table(
    "table_shows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("sonarrSeriesId", Integer, nullable=False, unique=True),
    Column("path", String, nullable=False),
    Column("title", String, nullable=False),
    Column("profileId", Integer, nullable=False),
    Column("imdbId", String, nullable=True),
    Column("tvdbId", Integer, nullable=True),
    Column("tags", String, nullable=False),
    Column("seriesType", String, nullable=False),
)
_movie_subtitle_rows = Table(
    "wanted_movie_subtitle_rows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("radarrId", Integer, nullable=False),
    Column("path", String, nullable=True),
    Column("language", String, nullable=False),
    Column("forced", Boolean, nullable=False),
    Column("hi", Boolean, nullable=False),
    Column("size", Integer, nullable=True),
    Column("embedded_track_id", Integer, nullable=True),
)
_episode_subtitle_rows = Table(
    "wanted_episode_subtitle_rows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("sonarrEpisodeId", Integer, nullable=False),
    Column("path", String, nullable=True),
    Column("language", String, nullable=False),
    Column("forced", Boolean, nullable=False),
    Column("hi", Boolean, nullable=False),
    Column("size", Integer, nullable=True),
    Column("embedded_track_id", Integer, nullable=True),
)
_movie_history_rows = Table(
    "wanted_movie_history_rows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("language", String, nullable=True),
    Column("video_path", String, nullable=True),
    Column("score", Integer, nullable=True),
    Column("score_out_of", Integer, nullable=True),
    Column("radarrId", Integer, nullable=False),
    Column("subtitles_path", String, nullable=True),
    Column("action", Integer, nullable=False),
    Column("timestamp", DateTime, nullable=True),
    Column("upgradedFromId", Integer, nullable=True),
)
_episode_history_rows = Table(
    "wanted_episode_history_rows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("language", String, nullable=True),
    Column("video_path", String, nullable=True),
    Column("score", Integer, nullable=True),
    Column("score_out_of", Integer, nullable=True),
    Column("sonarrEpisodeId", Integer, nullable=False),
    Column("sonarrSeriesId", Integer, nullable=False),
    Column("subtitles_path", String, nullable=True),
    Column("action", Integer, nullable=False),
    Column("timestamp", DateTime, nullable=True),
    Column("upgradedFromId", Integer, nullable=True),
)


class _TableProxy:
    def __init__(self, table):
        self._table = table
        for column in table.c:
            setattr(self, column.name, column)

    def __clause_element__(self):
        return self._table

    @property
    def c(self):
        return self._table.c


def _insert_row(session, table, values):
    session.execute(insert(table).values(**values))
    session.flush()
    return SimpleNamespace(**values)


def _serialize_missing_languages(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(list(dict.fromkeys(value)))


def _serialize_failed_attempts(value):
    if value is None:
        return "[]"
    if isinstance(value, str):
        return value
    return str(list(value))


def _infer_kind(request):
    if "kind" in request.fixturenames:
        try:
            return request.getfixturevalue("kind")
        except (pytest.FixtureLookupError, AttributeError):
            pass

    if "series" in request.node.name or "episode" in request.node.name:
        return "series"
    if "movie" in request.node.name:
        return "movies"
    if "episode_row_factory" in request.fixturenames or "show_row_factory" in request.fixturenames:
        return "series"
    return "movies"


def _infer_wanted_kind(request):
    return _infer_kind(request)


def _infer_mass_download_kind(request):
    return _infer_kind(request)


@pytest.fixture(scope="session")
def wanted_search_schema(transactional_engine):
    _metadata.create_all(transactional_engine)
    return _metadata


@pytest.fixture
def wanted_row_ids():
    return count(1)


@pytest.fixture
def wanted_search_tables():
    return SimpleNamespace(
        movie=_movie_rows,
        show=_show_rows,
        episode=_episode_rows,
        movie_subtitle=_movie_subtitle_rows,
        episode_subtitle=_episode_subtitle_rows,
        movie_history=_movie_history_rows,
        episode_history=_episode_history_rows,
    )


@pytest.fixture
def jobs_queue_factory():
    class _JobsQueueFake:
        def __init__(self, progress_updates=None, names=None):
            self._progress_updates = progress_updates
            self._names = names

        def add_job_from_function(self, *unused_args, **unused_kwargs):
            return None

        def update_job_progress(self, **kwargs):
            if self._progress_updates is not None:
                self._progress_updates.append(kwargs)

        def update_job_name(self, *unused_args, **kwargs):
            if self._names is not None:
                self._names.append(kwargs["new_job_name"])

    def factory(progress_updates=None, names=None):
        return _JobsQueueFake(progress_updates=progress_updates, names=names)

    return factory


@pytest.fixture
def movie_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema
    def factory(**overrides):
        missing_languages = overrides.pop("missing_languages", None)
        failed_attempts = overrides.pop("failed_attempts", None)
        values = {
            "id": next(wanted_row_ids),
            "path": "/movies/movie.mkv",
            "missing_subtitles": "['en', 'fr:forced']",
            "radarrId": 7,
            "audio_language": "['eng']",
            "sceneName": "Scene",
            "failedAttempts": "[['en', 10], ['fr:forced', 10]]",
            "title": "Movie",
            "year": 2024,
            "imdbId": "tt123",
            "tmdbId": 333,
            "profileId": 11,
            "tags": "[]",
            "monitored": True,
            "has_indexed_subtitles": True,
            "has_incomplete_embedded_subtitles": False,
        }
        if missing_languages is not None:
            values["missing_subtitles"] = _serialize_missing_languages(missing_languages)
        if failed_attempts is not None:
            values["failedAttempts"] = _serialize_failed_attempts(failed_attempts)
        values.update(overrides)
        return _insert_row(transactional_session, _movie_rows, values)

    return factory


@pytest.fixture
def show_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema
    def factory(**overrides):
        values = {
            "id": next(wanted_row_ids),
            "sonarrSeriesId": 3,
            "path": "/series",
            "title": "Series",
            "profileId": 22,
            "imdbId": "tt456",
            "tvdbId": 222,
            "tags": "[]",
            "seriesType": "standard",
        }
        values.update(overrides)
        return _insert_row(transactional_session, _show_rows, values)

    return factory


@pytest.fixture
def episode_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema
    def factory(**overrides):
        episode_title = overrides.pop("episodeTitle", "Pilot")
        missing_languages = overrides.pop("missing_languages", None)
        failed_attempts = overrides.pop("failed_attempts", None)
        values = {
            "id": next(wanted_row_ids),
            "path": "/series/e01.mkv",
            "missing_subtitles": "['en', 'fr:hi']",
            "sonarrEpisodeId": 17,
            "sonarrSeriesId": 3,
            "audio_language": "['eng']",
            "sceneName": "Scene",
            "failedAttempts": "[['en', 10], ['fr:hi', 10]]",
            "title": "Series",
            "profileId": 22,
            "season": 1,
            "episode": 1,
            "episodeTitle": episode_title,
            "monitored": True,
            "has_indexed_subtitles": True,
            "has_incomplete_embedded_subtitles": False,
        }
        if missing_languages is not None:
            values["missing_subtitles"] = _serialize_missing_languages(missing_languages)
        if failed_attempts is not None:
            values["failedAttempts"] = _serialize_failed_attempts(failed_attempts)
        values.update(overrides)

        existing_show = transactional_session.execute(
            _show_rows.select().where(_show_rows.c.sonarrSeriesId == values["sonarrSeriesId"])
        ).first()
        if not existing_show:
            _insert_row(
                transactional_session,
                _show_rows,
                {
                    "id": next(wanted_row_ids),
                    "sonarrSeriesId": values["sonarrSeriesId"],
                    "path": "/series",
                    "title": values.get("title") or "Series",
                    "profileId": values["profileId"],
                    "imdbId": "tt456",
                    "tvdbId": 222,
                    "tags": "[]",
                    "seriesType": "standard",
                },
            )

        episode_values = dict(values, title=values.get("episodeTitle") or episode_title)
        return _insert_row(transactional_session, _episode_rows, episode_values)

    return factory


@pytest.fixture
def row_factory(request, movie_row_factory, episode_row_factory):
    kind = _infer_wanted_kind(request)
    if kind == "movies":
        return movie_row_factory
    if kind == "series":
        return episode_row_factory
    raise ValueError(f"Unsupported wanted kind: {kind}")


@pytest.fixture
def movie_subtitle_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema

    def factory(**overrides):
        values = {
            "id": next(wanted_row_ids),
            "radarrId": 7,
            "path": "/movies/sub.srt",
            "language": "en",
            "forced": False,
            "hi": False,
            "size": 123,
            "embedded_track_id": 1,
        }
        values.update(overrides)
        return _insert_row(transactional_session, _movie_subtitle_rows, values)

    return factory


@pytest.fixture
def episode_subtitle_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema

    def factory(**overrides):
        values = {
            "id": next(wanted_row_ids),
            "sonarrEpisodeId": 17,
            "path": "/series/sub.srt",
            "language": "en",
            "forced": False,
            "hi": False,
            "size": 123,
            "embedded_track_id": 1,
        }
        values.update(overrides)
        return _insert_row(transactional_session, _episode_subtitle_rows, values)

    return factory


@pytest.fixture
def movie_history_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema

    def factory(**overrides):
        values = {
            "id": next(wanted_row_ids),
            "language": "en",
            "video_path": "/movies/movie.mkv",
            "score": 80,
            "score_out_of": 120,
            "radarrId": 7,
            "subtitles_path": "/movies/sub.srt",
            "action": 1,
            "timestamp": None,
            "upgradedFromId": None,
        }
        values.update(overrides)
        return _insert_row(transactional_session, _movie_history_rows, values)

    return factory


@pytest.fixture
def episode_history_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema

    def factory(**overrides):
        values = {
            "id": next(wanted_row_ids),
            "language": "en",
            "video_path": "/series/e01.mkv",
            "score": 80,
            "score_out_of": 360,
            "sonarrEpisodeId": 17,
            "sonarrSeriesId": 3,
            "subtitles_path": "/series/sub.srt",
            "action": 1,
            "timestamp": None,
            "upgradedFromId": None,
        }
        values.update(overrides)
        return _insert_row(transactional_session, _episode_history_rows, values)

    return factory


@pytest.fixture
def bind_wanted_database(transactional_session, wanted_search_schema, monkeypatch):
    del wanted_search_schema

    def get_profile_id(*, movie_id=None, episode_id=None, **unused_kwargs):
        if movie_id is not None:
            statement = select(_movie_rows.c.profileId).where(_movie_rows.c.radarrId == movie_id)
        elif episode_id is not None:
            statement = select(_episode_rows.c.profileId).where(_episode_rows.c.sonarrEpisodeId == episode_id)
        else:
            return None

        return transactional_session.execute(statement).scalar_one_or_none()

    def get_profiles_list(*unused_args, **unused_kwargs):
        return {"items": [], "originalFormat": False}

    def get_audio_profile_languages(audio_languages):
        if audio_languages in (None, "", "[]"):
            return []
        return [{"name": "English", "code2": "en", "code3": "eng"}]

    def get_subtitles(*, sonarr_episode_id=None, radarr_id=None):
        if sonarr_episode_id is not None:
            rows = transactional_session.execute(
                select(_episode_subtitle_rows).where(_episode_subtitle_rows.c.sonarrEpisodeId == sonarr_episode_id)
            ).mappings().all()
        elif radarr_id is not None:
            rows = transactional_session.execute(
                select(_movie_subtitle_rows).where(_movie_subtitle_rows.c.radarrId == radarr_id)
            ).mappings().all()
        else:
            rows = []

        subtitles = []
        for subtitle in rows:
            subtitles.append(
                {
                    "path": subtitle.path,
                    "name": subtitle.language,
                    "code2": subtitle.language,
                    "code3": subtitle.language,
                    "forced": subtitle.forced,
                    "hi": subtitle.hi,
                    "file_size": subtitle.size,
                    "embedded_track_id": subtitle.embedded_track_id,
                }
            )
        return subtitles

    def bind(module, kind):
        monkeypatch.setattr(module, "database", transactional_session, raising=False)
        monkeypatch.setattr(module, "select", select, raising=False)
        monkeypatch.setattr(module, "update", update, raising=False)
        monkeypatch.setattr(module, "get_profile_id", get_profile_id, raising=False)
        monkeypatch.setattr(module, "get_profiles_list", get_profiles_list, raising=False)
        monkeypatch.setattr(module, "get_audio_profile_languages", get_audio_profile_languages, raising=False)
        monkeypatch.setattr(module, "get_subtitles", get_subtitles, raising=False)

        if kind == "movies":
            monkeypatch.setattr(module, "TableMovies", _TableProxy(_movie_rows), raising=False)
        elif kind == "series":
            monkeypatch.setattr(module, "TableEpisodes", _TableProxy(_episode_rows), raising=False)
            monkeypatch.setattr(module, "TableShows", _TableProxy(_show_rows), raising=False)
        else:
            raise ValueError(f"Unsupported wanted database kind: {kind}")

        if kind == "movies":
            monkeypatch.setattr(module, "TableHistoryMovie", _TableProxy(_movie_history_rows), raising=False)
            monkeypatch.setattr(module, "TableMoviesSubtitles", _TableProxy(_movie_subtitle_rows), raising=False)
        elif kind == "series":
            monkeypatch.setattr(module, "TableHistory", _TableProxy(_episode_history_rows), raising=False)
            monkeypatch.setattr(module, "TableEpisodesSubtitles", _TableProxy(_episode_subtitle_rows), raising=False)

        return module

    return bind


@pytest.fixture
def wanted_module(request, bind_wanted_database):
    kind = _infer_wanted_kind(request)
    module_name = {
        "movies": "subtitles.wanted.movies",
        "series": "subtitles.wanted.series",
    }.get(kind)
    if not module_name:
        raise ValueError(f"Unsupported wanted kind: {kind}")

    module = importlib.import_module(module_name)
    return bind_wanted_database(module, kind)


@pytest.fixture
def wanted_download_subtitles(request, wanted_module):
    kind = _infer_wanted_kind(request)
    if kind == "movies":
        return wanted_module.wanted_download_subtitles_movie
    if kind == "series":
        return wanted_module.wanted_download_subtitles
    raise ValueError(f"Unsupported wanted kind: {kind}")


@pytest.fixture
def wanted_search_job(request, wanted_module):
    kind = _infer_wanted_kind(request)
    if kind == "movies":
        return wanted_module.wanted_search_missing_subtitles_movies
    if kind == "series":
        return wanted_module.wanted_search_missing_subtitles_series
    raise ValueError(f"Unsupported wanted kind: {kind}")


@pytest.fixture
def mass_download_module(request, bind_wanted_database):
    kind = _infer_mass_download_kind(request)
    module_name = {
        "movies": "subtitles.mass_download.movies",
        "series": "subtitles.mass_download.series",
    }.get(kind)
    if not module_name:
        raise ValueError(f"Unsupported mass-download kind: {kind}")

    module = importlib.import_module(module_name)
    return bind_wanted_database(module, kind)
