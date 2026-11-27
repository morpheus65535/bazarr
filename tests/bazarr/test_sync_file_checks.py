import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import TableEpisodes, TableMovies
from constants import MINIMUM_VIDEO_SIZE
from radarr.sync import movies
from sonarr.sync import episodes, parser
from tests.bazarr.test_sync_lookups import configure_episodes, configure_movies


@pytest.mark.parametrize('kind', ['movie', 'episode'])
@pytest.mark.parametrize('strm', [False, True])
def test_sync_stats_undersized_files_once(kind: str, strm: bool, memory_session: Session,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    files = ([record.movieFile for record in configure_movies(monkeypatch, memory_session, 3)] if kind == 'movie'
             else [record.episodeFile for record in configure_episodes(monkeypatch, memory_session, 3)])
    for file in files:
        assert file is not None
        file.size = 0
        if strm:
            file.path = file.path.replace('.mkv', '.strm')
    stats: list[str] = []

    def getsize(path: str) -> int:
        stats.append(path)
        return 0 if strm else MINIMUM_VIDEO_SIZE + 1

    monkeypatch.setattr(parser.os.path, 'getsize', getsize)
    monkeypatch.setattr(parser.settings.general, 'enable_strm_support', strm)
    monkeypatch.setattr(movies, 'store_subtitles_movie', lambda identifier: None)
    monkeypatch.setattr(episodes, 'store_subtitles', lambda identifier: None)
    if kind == 'movie':
        movies.update_movies(job_id=1)
        sizes = memory_session.execute(select(TableMovies.file_size)).scalars().all()
    else:
        episodes.sync_episodes(7, defer_search=True)
        sizes = memory_session.execute(select(TableEpisodes.file_size)).scalars().all()

    assert len(stats) == 3
    assert sizes == [0, 0, 0]  # Persist the Arr size, not the filesystem fallback.


def test_movie_size_cache_keeps_strm_setting_live(memory_session: Session,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    record = configure_movies(monkeypatch, memory_session, 1)[0]
    assert record.movieFile is not None
    record.movieFile.path = '/movie.strm'
    record.movieFile.size = 0
    monkeypatch.setattr(movies, 'get_movie_file_size_from_db', lambda path: 0)
    sizes: dict[str, int] = {}
    monkeypatch.setattr(movies.settings.general, 'enable_strm_support', False)
    assert not movies._has_usable_movie_file(record, file_sizes=sizes)
    monkeypatch.setattr(movies.settings.general, 'enable_strm_support', True)
    assert movies._has_usable_movie_file(record, file_sizes=sizes)


def test_standalone_episode_parser_handles_missing_file(monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.helpers.arr_fixtures import episode_payload, episode_record

    record = episode_record(episode_payload())
    assert record.episodeFile is not None
    record.episodeFile.size = 0
    monkeypatch.setattr(parser.settings.general, 'enable_strm_support', False)

    def missing(path: str) -> int:
        raise FileNotFoundError(path)

    monkeypatch.setattr(parser.os.path, 'getsize', missing)
    assert parser.episodeParser(record) is None
