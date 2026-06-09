from itertools import count
from types import SimpleNamespace

import pytest
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import insert

_metadata = MetaData()
_movie_rows = Table(
    "wanted_movie_rows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("path", String, nullable=False),
    Column("missing_subtitles", String, nullable=True),
    Column("radarrId", Integer, nullable=False),
    Column("audio_language", String, nullable=False),
    Column("sceneName", String, nullable=True),
    Column("failedAttempts", String, nullable=False),
    Column("title", String, nullable=False),
    Column("profileId", Integer, nullable=False),
    Column("tags", String, nullable=False),
    Column("monitored", Boolean, nullable=False),
    Column("has_indexed_subtitles", Boolean, nullable=False),
    Column("has_incomplete_embedded_subtitles", Boolean, nullable=False),
)
_episode_rows = Table(
    "wanted_episode_rows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("path", String, nullable=False),
    Column("missing_subtitles", String, nullable=True),
    Column("sonarrEpisodeId", Integer, nullable=False),
    Column("sonarrSeriesId", Integer, ForeignKey("wanted_show_rows.sonarrSeriesId"), nullable=False),
    Column("audio_language", String, nullable=False),
    Column("sceneName", String, nullable=True),
    Column("failedAttempts", String, nullable=False),
    Column("title", String, nullable=False),
    Column("profileId", Integer, nullable=False),
    Column("season", Integer, nullable=False),
    Column("episode", Integer, nullable=False),
    Column("episodeTitle", String, nullable=False),
    Column("monitored", Boolean, nullable=False),
    Column("has_indexed_subtitles", Boolean, nullable=False),
    Column("has_incomplete_embedded_subtitles", Boolean, nullable=False),
)
_show_rows = Table(
    "wanted_show_rows",
    _metadata,
    Column("id", Integer, primary_key=True),
    Column("sonarrSeriesId", Integer, nullable=False, unique=True),
    Column("title", String, nullable=False),
    Column("profileId", Integer, nullable=False),
    Column("tags", String, nullable=False),
    Column("seriesType", String, nullable=False),
)

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
    )


def _insert_row(session, table, values):
    session.execute(insert(table).values(**values))
    session.flush()
    return SimpleNamespace(**values)


@pytest.fixture
def movie_row_factory(transactional_session, wanted_search_schema, wanted_row_ids):
    del wanted_search_schema

    def factory(**overrides):
        values = {
            "id": next(wanted_row_ids),
            "path": "/movies/movie.mkv",
            "missing_subtitles": "['en', 'fr:forced']",
            "radarrId": 7,
            "audio_language": "['eng']",
            "sceneName": "Scene",
            "failedAttempts": "[['en', 10], ['fr:forced', 10]]",
            "title": "Movie",
            "profileId": 11,
            "tags": "[]",
            "monitored": True,
            "has_indexed_subtitles": True,
            "has_incomplete_embedded_subtitles": False,
        }
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
            "title": "Series",
            "profileId": 22,
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
            "episodeTitle": "Pilot",
            "monitored": True,
            "has_indexed_subtitles": True,
            "has_incomplete_embedded_subtitles": False,
        }
        values.update(overrides)
        return _insert_row(transactional_session, _episode_rows, values)

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

    def bind(module, kind):
        monkeypatch.setattr(module, "database", transactional_session, raising=False)
        monkeypatch.setattr(module, "select", select, raising=False)
        monkeypatch.setattr(module, "update", update, raising=False)
        monkeypatch.setattr(module, "get_profile_id", get_profile_id, raising=False)
        monkeypatch.setattr(module, "get_profiles_list", get_profiles_list, raising=False)

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
def wanted_worker(request, wanted_module):
    kind = _infer_wanted_kind(request)
    if kind == "movies":
        return wanted_module._wanted_movie
    if kind == "series":
        return wanted_module._wanted_episode
    raise ValueError(f"Unsupported wanted kind: {kind}")


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
