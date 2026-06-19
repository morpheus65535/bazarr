import importlib
import os
from itertools import count
from types import SimpleNamespace

import pytest
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import UniqueConstraint
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

os.environ.setdefault("SZ_USER_AGENT", "pytest")

from subtitles.wanted_state import serialize_legacy_failed_attempts

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
_missing_subtitle_rows = Table(
    "table_missing_subtitles",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("media_type", String, nullable=False),
    Column("media_id", Integer, nullable=False),
    Column("language", String, nullable=False),
)
_failed_subtitle_attempt_rows = Table(
    "table_failed_subtitle_attempts",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("media_type", String, nullable=False),
    Column("media_id", Integer, nullable=False),
    Column("language", String, nullable=False),
    Column("initial_attempt_at", Float, nullable=False),
    Column("latest_attempt_at", Float, nullable=False),
    UniqueConstraint("media_type", "media_id", "language"),
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


def _serialize_failed_attempts(failed_attempts):
    if failed_attempts is None:
        return "[]"
    if isinstance(failed_attempts, str):
        return failed_attempts

    attempts_by_language = {}
    for attempt in failed_attempts:
        if not isinstance(attempt, (list, tuple)) or len(attempt) < 2 or not isinstance(attempt[0], str):
            continue
        try:
            timestamp = float(attempt[1])
        except (TypeError, ValueError):
            continue
        initial_attempt_at, latest_attempt_at = attempts_by_language.get(attempt[0], (timestamp, timestamp))
        attempts_by_language[attempt[0]] = (
            min(initial_attempt_at, timestamp),
            max(latest_attempt_at, timestamp),
        )

    return serialize_legacy_failed_attempts(attempts_by_language)


def _seed_wanted_state(media_type, media_id, missing_languages, failed_attempts):
    wanted_state = importlib.import_module("subtitles.wanted_state")
    wanted_state.refresh_wanted_search_state(
        media_type,
        media_id,
        missing_languages,
        failed_attempts=failed_attempts,
    )


def _bind_movie_selects(module):
    details_select = select(
        module.TableMovies.path,
        module.TableMovies.missing_subtitles,
        module.TableMovies.radarrId,
        module.TableMovies.audio_language,
        module.TableMovies.sceneName,
        module.TableMovies.failedAttempts,
        module.TableMovies.title,
        module.TableMovies.profileId,
        select(module.TableMoviesSubtitles.id)
        .where(module.TableMoviesSubtitles.radarrId == module.TableMovies.radarrId)
        .limit(1)
        .exists()
        .label("has_indexed_subtitles"),
        select(module.TableMoviesSubtitles.id)
        .where(module.TableMoviesSubtitles.radarrId == module.TableMovies.radarrId)
        .where(module.TableMoviesSubtitles.path.is_(None))
        .where(module.TableMoviesSubtitles.embedded_track_id.is_(None))
        .limit(1)
        .exists()
        .label("has_incomplete_embedded_subtitles"),
    )
    module._WANTED_MOVIE_DETAILS_SELECT = details_select
    module._WANTED_MOVIE_DETAILS_STMT = details_select.where(
        module.TableMovies.radarrId == module.bindparam("wanted_radarr_id")
    )
    module._WANTED_MOVIES_SELECT = select(
        module.TableMovies.radarrId,
        module.TableMovies.audio_language,
        module.TableMovies.failedAttempts,
        module.TableMovies.missing_subtitles,
        module.TableMovies.path,
        module.TableMovies.profileId,
        module.TableMovies.sceneName,
        module.TableMovies.tags,
        module.TableMovies.monitored,
        module.TableMovies.title,
        select(module.TableMoviesSubtitles.id)
        .where(module.TableMoviesSubtitles.radarrId == module.TableMovies.radarrId)
        .limit(1)
        .exists()
        .label("has_indexed_subtitles"),
        select(module.TableMoviesSubtitles.id)
        .where(module.TableMoviesSubtitles.radarrId == module.TableMovies.radarrId)
        .where(module.TableMoviesSubtitles.path.is_(None))
        .where(module.TableMoviesSubtitles.embedded_track_id.is_(None))
        .limit(1)
        .exists()
        .label("has_incomplete_embedded_subtitles"),
    )


def _bind_episode_selects(module):
    details_select = (
        select(
            module.TableEpisodes.path,
            module.TableEpisodes.missing_subtitles,
            module.TableEpisodes.sonarrEpisodeId,
            module.TableEpisodes.sonarrSeriesId,
            module.TableEpisodes.audio_language,
            module.TableEpisodes.sceneName,
            module.TableEpisodes.failedAttempts,
            module.TableShows.title,
            module.TableShows.profileId,
            module.TableEpisodes.season,
            module.TableEpisodes.episode,
            module.TableEpisodes.title.label("episodeTitle"),
            select(module.TableEpisodesSubtitles.id)
            .where(module.TableEpisodesSubtitles.sonarrEpisodeId == module.TableEpisodes.sonarrEpisodeId)
            .limit(1)
            .exists()
            .label("has_indexed_subtitles"),
            select(module.TableEpisodesSubtitles.id)
            .where(module.TableEpisodesSubtitles.sonarrEpisodeId == module.TableEpisodes.sonarrEpisodeId)
            .where(module.TableEpisodesSubtitles.path.is_(None))
            .where(module.TableEpisodesSubtitles.embedded_track_id.is_(None))
            .limit(1)
            .exists()
            .label("has_incomplete_embedded_subtitles"),
        )
        .select_from(module.TableEpisodes)
        .join(module.TableShows)
    )
    module._WANTED_EPISODE_DETAILS_SELECT = details_select
    module._WANTED_EPISODE_DETAILS_STMT = details_select.where(
        module.TableEpisodes.sonarrEpisodeId == module.bindparam("wanted_sonarr_episode_id")
    )


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
        missing_subtitles=_missing_subtitle_rows,
        failed_subtitle_attempts=_failed_subtitle_attempt_rows,
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
def bind_wanted_state(transactional_session, wanted_search_schema, monkeypatch):
    del wanted_search_schema
    wanted_state = importlib.import_module("subtitles.wanted_state")
    missing_subtitles = _TableProxy(_missing_subtitle_rows)
    failed_subtitle_attempts = _TableProxy(_failed_subtitle_attempt_rows)

    monkeypatch.setattr(wanted_state, "database", transactional_session, raising=False)
    monkeypatch.setattr(wanted_state, "TableMissingSubtitles", missing_subtitles, raising=False)
    monkeypatch.setattr(wanted_state, "TableFailedSubtitleAttempts", failed_subtitle_attempts, raising=False)


@pytest.fixture
def movie_row_factory(transactional_session, bind_wanted_state, wanted_row_ids):
    del bind_wanted_state

    def factory(**overrides):
        missing_languages = overrides.pop("missing_languages", ["en", "fr:forced"])
        failed_attempts = overrides.pop("failed_attempts", [("en", 10), ("fr:forced", 10)])
        values = {
            "id": next(wanted_row_ids),
            "path": "/movies/movie.mkv",
            "missing_subtitles": _serialize_missing_languages(missing_languages),
            "radarrId": 7,
            "audio_language": "['eng']",
            "sceneName": "Scene",
            "failedAttempts": _serialize_failed_attempts(failed_attempts),
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
        values.update(overrides)
        row = _insert_row(transactional_session, _movie_rows, values)
        _seed_wanted_state(
            "movie",
            values["radarrId"],
            values.get("missing_subtitles"),
            values.get("failedAttempts"),
        )
        return row

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
def episode_row_factory(transactional_session, bind_wanted_state, wanted_row_ids):
    del bind_wanted_state

    def factory(**overrides):
        episode_title = overrides.pop("episodeTitle", "Pilot")
        missing_languages = overrides.pop("missing_languages", ["en", "fr:hi"])
        failed_attempts = overrides.pop("failed_attempts", [("en", 10), ("fr:hi", 10)])
        values = {
            "id": next(wanted_row_ids),
            "path": "/series/e01.mkv",
            "missing_subtitles": _serialize_missing_languages(missing_languages),
            "sonarrEpisodeId": 17,
            "sonarrSeriesId": 3,
            "audio_language": "['eng']",
            "sceneName": "Scene",
            "failedAttempts": _serialize_failed_attempts(failed_attempts),
            "title": "Series",
            "profileId": 22,
            "season": 1,
            "episode": 1,
            "episodeTitle": episode_title,
            "monitored": True,
            "has_indexed_subtitles": True,
            "has_incomplete_embedded_subtitles": False,
        }
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
        row = _insert_row(transactional_session, _episode_rows, episode_values)
        _seed_wanted_state(
            "series",
            values["sonarrEpisodeId"],
            values.get("missing_subtitles"),
            values.get("failedAttempts"),
        )
        return row

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
def bind_wanted_database(transactional_session, bind_wanted_state, monkeypatch):
    del bind_wanted_state

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
        wanted_state = importlib.import_module("subtitles.wanted_state")

        monkeypatch.setattr(module, "database", transactional_session, raising=False)
        monkeypatch.setattr(module, "select", select, raising=False)
        monkeypatch.setattr(module, "update", update, raising=False)
        monkeypatch.setattr(module, "get_profile_id", get_profile_id, raising=False)
        monkeypatch.setattr(module, "get_profiles_list", get_profiles_list, raising=False)
        monkeypatch.setattr(module, "get_audio_profile_languages", get_audio_profile_languages, raising=False)
        monkeypatch.setattr(module, "get_subtitles", get_subtitles, raising=False)
        monkeypatch.setattr(module, "TableMissingSubtitles", _TableProxy(_missing_subtitle_rows), raising=False)
        monkeypatch.setattr(
            module,
            "TableFailedSubtitleAttempts",
            _TableProxy(_failed_subtitle_attempt_rows),
            raising=False,
        )
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
            if hasattr(module, "_WANTED_MOVIE_DETAILS_SELECT"):
                _bind_movie_selects(module)
        elif kind == "series":
            monkeypatch.setattr(module, "TableHistory", _TableProxy(_episode_history_rows), raising=False)
            monkeypatch.setattr(module, "TableEpisodesSubtitles", _TableProxy(_episode_subtitle_rows), raising=False)
            if hasattr(module, "_WANTED_EPISODE_DETAILS_SELECT"):
                _bind_episode_selects(module)

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
