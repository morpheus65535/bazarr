from collections.abc import Iterator, Mapping, Sequence
from copy import deepcopy
from threading import Event
from types import SimpleNamespace
from typing import TypeAlias

import pytest
from sqlalchemy import delete, event, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.engine.interfaces import DBAPICursor, ExecutionContext
from sqlalchemy.orm import Session

from app.database import TableEpisodes, TableMovies, TableShows
from radarr.movie_snapshot import Movie
from radarr.sync import movies, parser as movie_parser
from radarr.sync.utils import MOVIE_DECODER
from sonarr.episode_snapshot import Episode
from sonarr.sync import episodes, parser as episode_parser
from utilities.arr_sync_lookups import ArrSyncLookups
from tests.helpers.arr_fixtures import episode_payload, episode_record, movie_payload


SqlValue: TypeAlias = str | int | float | bytes | None
SqlParameters: TypeAlias = Mapping[str, SqlValue] | Sequence[SqlValue]


@pytest.fixture
def sql_reads(memory_session: Session) -> Iterator[list[str]]:
    reads: list[str] = []
    engine = memory_session.get_bind()

    def record(connection: Connection, cursor: DBAPICursor, statement: str, parameters: SqlParameters,
               context: ExecutionContext, executemany: bool) -> None:
        if statement.lstrip().startswith('SELECT'):
            reads.append(statement)

    event.listen(engine, 'before_cursor_execute', record)
    try:
        yield reads
    finally:
        event.remove(engine, 'before_cursor_execute', record)


def configure_movies(monkeypatch: pytest.MonkeyPatch, session: Session, count: int,
                     *, monitored_only: bool = False) -> list[Movie]:
    monkeypatch.setattr(movies, 'database', session)
    monkeypatch.setattr(movie_parser.get_radarr_info, 'is_legacy', lambda: False)
    for name in ('movie_default_enabled', 'movie_tag_enabled', 'parse_embedded_audio_track', 'debug'):
        monkeypatch.setattr(movies.settings.general, name, False)
    monkeypatch.setattr(movies.settings.radarr, 'apikey', 'key')
    monkeypatch.setattr(movies.settings.radarr, 'sync_only_monitored_movies', monitored_only)
    monkeypatch.setattr(movies, 'check_radarr_rootfolder', lambda: None)
    monkeypatch.setattr(movies, 'get_profile_list', lambda: [])
    monkeypatch.setattr(movies, 'get_tags', lambda: [])
    monkeypatch.setattr(movies, 'get_language_profiles', lambda: [])
    monkeypatch.setattr(movies, 'store_subtitles_movie', lambda identifier: pytest.fail('File identity did not change'))
    monkeypatch.setattr(movies, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(movies, 'jobs_queue', SimpleNamespace(
        get_job=lambda **kwargs: SimpleNamespace(cancel_event=Event()),
        update_job_progress=lambda **kwargs: None,
        update_job_name=lambda **kwargs: None,
    ))
    records: list[Movie] = []
    for identifier in range(1, count + 1):
        record = MOVIE_DECODER.complete_from_value(movie_payload(
            movie_id=identifier, path=f'/movies/{identifier}.mkv', file_id=identifier + 1000))
        assert isinstance(record, Movie)
        values = movie_parser.movieParser(record, 'insert', ArrSyncLookups([], [], []), None)
        session.add(TableMovies(**values))
        record.title = f'Changed {identifier}'
        records.append(record)
    session.commit()
    monkeypatch.setattr(movies, 'get_movies_from_radarr_api', lambda **kwargs: records)
    return records


def configure_episodes(monkeypatch: pytest.MonkeyPatch, session: Session, count: int) -> list[Episode]:
    monkeypatch.setattr(episodes, 'database', session)
    monkeypatch.setattr(episode_parser, 'database', session)
    monkeypatch.setattr(episodes.settings.general, 'parse_embedded_audio_track', False)
    monkeypatch.setattr(episodes.settings.sonarr, 'sync_only_monitored_series', False)
    monkeypatch.setattr(episodes, '_validated_episodes', lambda records, **kwargs: records)
    monkeypatch.setattr(episodes, 'store_subtitles', lambda identifier: pytest.fail('File identity did not change'))
    monkeypatch.setattr(episodes, 'event_stream', lambda **kwargs: None)
    session.add(TableShows(sonarrSeriesId=7, title='Show', path='/show', audio_language="['English']"))
    session.flush()
    records: list[Episode] = []
    for identifier in range(1, count + 1):
        record = episode_record(episode_payload(episode_id=identifier))
        assert record.episodeFile is not None
        record.episodeFile.id = identifier + 1000
        record.episodeFile.path = f'/show/{identifier}.mkv'
        values = episode_parser.episodeParser(record, parse_embedded_audio_track=False)
        assert values is not None
        session.add(TableEpisodes(**values))
        record.title = f'Changed {identifier}'
        records.append(record)
    session.commit()
    monkeypatch.setattr(episodes, 'get_episodes_from_sonarr_api', lambda **kwargs: records)
    return records


@pytest.mark.parametrize('count', [1, 20, 205])
@pytest.mark.parametrize('monitored_only', [False, True])
def test_movie_reads_do_not_grow_with_catalogue(count: int, monitored_only: bool, memory_session: Session,
                                               monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    configure_movies(monkeypatch, memory_session, count, monitored_only=monitored_only)
    sql_reads.clear()

    movies.update_movies(job_id=1)

    assert len(sql_reads) == 1
    assert memory_session.execute(select(TableMovies.title)).scalars().all() == [
        f'Changed {identifier}' for identifier in range(1, count + 1)]


def test_unchanged_movies_do_not_read_file_metadata(memory_session: Session,
                                                   monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_movies(monkeypatch, memory_session, 20)
    for record in records:
        record.title = 'Movie'
    sql_reads.clear()

    movies.update_movies(job_id=1)

    assert len(sql_reads) == 1


def test_movie_file_changes_use_loaded_state(memory_session: Session,
                                              monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_movies(monkeypatch, memory_session, 1)
    file = records[0].movieFile
    assert file is not None
    file.id += 1
    file.path = '/movies/replaced.mkv'
    indexed: list[int] = []
    monkeypatch.setattr(movies, 'store_subtitles_movie', indexed.append)
    sql_reads.clear()

    movies.update_movies(job_id=1)

    assert len(sql_reads) == 1
    assert indexed == [1]
    assert memory_session.execute(select(TableMovies.path)).scalar_one() == file.path


@pytest.mark.parametrize('stored_monitored', [True, False])
@pytest.mark.parametrize('count', [1, 20, 205])
def test_unmonitored_movies_use_loaded_state(stored_monitored: bool, count: int, memory_session: Session,
                                            monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_movies(monkeypatch, memory_session, count, monitored_only=True)
    for record in records:
        record.monitored = False
    memory_session.execute(update(TableMovies).values(monitored=str(stored_monitored)))
    sql_reads.clear()

    movies.update_movies(job_id=1)

    assert len(sql_reads) == 1
    expected_titles = [f'Changed {identifier}' if stored_monitored else 'Movie'
                       for identifier in range(1, count + 1)]
    assert memory_session.execute(select(TableMovies.title)).scalars().all() == expected_titles
    assert memory_session.execute(select(TableMovies.monitored)).scalars().all() == ['False'] * count


def test_monitored_guard_refreshes_on_next_sync(memory_session: Session,
                                               monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_movies(monkeypatch, memory_session, 2, monitored_only=True)
    records[-1].monitored = False

    def unmonitor_next_movie(*, type: str, action: str, payload: int) -> None:
        memory_session.execute(update(TableMovies).where(TableMovies.radarrId == 2).values(monitored='False'))

    monkeypatch.setattr(movies, 'event_stream', unmonitor_next_movie)
    sql_reads.clear()
    movies.update_movies(job_id=1)

    assert len(sql_reads) == 1
    assert memory_session.execute(select(TableMovies.title)).scalars().all() == ['Changed 1', 'Changed 2']

    records[-1].title = 'Next sync'
    sql_reads.clear()
    movies.update_movies(job_id=1)
    assert len(sql_reads) == 1
    assert memory_session.execute(select(TableMovies.title)).scalars().all() == ['Changed 1', 'Changed 2']


def test_new_unmonitored_movie_is_still_inserted(memory_session: Session, monkeypatch: pytest.MonkeyPatch,
                                               sql_reads: list[str]) -> None:
    records = configure_movies(monkeypatch, memory_session, 1, monitored_only=True)
    records[0].monitored = False
    memory_session.execute(delete(TableMovies))
    indexed: list[int] = []
    monkeypatch.setattr(movies, 'store_subtitles_movie', indexed.append)
    sql_reads.clear()

    movies.update_movies(job_id=1)

    assert len(sql_reads) == 1
    assert indexed == [1]
    assert memory_session.execute(select(TableMovies.monitored)).scalar_one() == 'False'


@pytest.mark.parametrize('count', [1, 20, 205])
@pytest.mark.parametrize('missing_language', [False, True])
def test_episode_reads_do_not_grow_with_series(count: int, missing_language: bool, memory_session: Session,
                                              monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_episodes(monkeypatch, memory_session, count)
    if missing_language:
        for record in records:
            assert record.episodeFile is not None
            record.episodeFile.language = None
    sql_reads.clear()

    episodes.sync_episodes(7, defer_search=True)

    assert len(sql_reads) == 2 + int(missing_language)
    assert memory_session.execute(select(TableEpisodes.title)).scalars().all() == [
        f'Changed {identifier}' for identifier in range(1, count + 1)]


@pytest.mark.parametrize('stored', ["['English']", None])
def test_episode_language_fallback_is_once_per_series(stored: str | None, memory_session: Session,
                                                    monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    monkeypatch.setattr(episode_parser, 'database', memory_session)
    memory_session.add_all([TableShows(sonarrSeriesId=identifier, title='Show', path=f'/show/{identifier}',
                                      audio_language=stored) for identifier in (7, 8)])
    memory_session.commit()
    cache: dict[int, str | None] = {}
    sql_reads.clear()
    for series_id in (7, 7, 8, 8, 7):
        record = episode_record(episode_payload(series_id=series_id))
        assert record.episodeFile is not None
        record.episodeFile.language = None
        values = episode_parser.episodeParser(record, parse_embedded_audio_track=False, audio_languages=cache)
        assert values is not None
        assert values['audio_language'] == str(stored)
    assert len(sql_reads) == 2

    memory_session.execute(update(TableShows).values(audio_language="['French']"))
    sql_reads.clear()
    record = episode_record(episode_payload())
    assert record.episodeFile is not None
    record.episodeFile.language = None
    values = episode_parser.episodeParser(record, parse_embedded_audio_track=False, audio_languages={})
    assert values is not None
    assert values['audio_language'] == "['French']"
    assert len(sql_reads) == 1


def test_duplicate_movie_rows_use_the_last_written_state(memory_session: Session,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    records = configure_movies(monkeypatch, memory_session, 1)
    assert records[0].movieFile is not None
    records[0].movieFile.id += 1
    records.append(deepcopy(records[0]))
    indexed: list[int] = []
    monkeypatch.setattr(movies, 'store_subtitles_movie', indexed.append)

    movies.update_movies(job_id=1)

    assert indexed == [1]


def test_episode_file_changes_use_loaded_state(memory_session: Session,
                                                monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_episodes(monkeypatch, memory_session, 1)
    assert records[0].episodeFile is not None
    records[0].episodeFile.id += 1
    indexed: list[int] = []
    monkeypatch.setattr(episodes, 'store_subtitles', indexed.append)
    sql_reads.clear()

    episodes.sync_episodes(7, defer_search=True)

    assert len(sql_reads) == 2
    assert indexed == [1]


def test_unchanged_episodes_do_not_read_file_metadata(memory_session: Session,
                                                     monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_episodes(monkeypatch, memory_session, 20)
    for record in records:
        record.title = 'Pilot'
    sql_reads.clear()

    episodes.sync_episodes(7, defer_search=True)

    assert len(sql_reads) == 2


def test_movie_cancellation_keeps_completed_writes(memory_session: Session,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    configure_movies(monkeypatch, memory_session, 2)
    canceled = Event()
    monkeypatch.setattr(movies.jobs_queue, 'get_job', lambda **kwargs: SimpleNamespace(cancel_event=canceled))

    def cancel(*, type: str, action: str, payload: int) -> None:
        canceled.set()

    monkeypatch.setattr(movies, 'event_stream', cancel)
    with pytest.raises(movies.JobCanceled):
        movies.update_movies(job_id=1)
    assert memory_session.execute(select(TableMovies.title)).scalars().all() == ['Changed 1', 'Movie']


def test_episode_insert_collision_reads_the_new_row(memory_session: Session,
                                                    monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_episodes(monkeypatch, memory_session, 1)
    stored_values = episode_parser.episodeParser(records[0], parse_embedded_audio_track=False)
    assert stored_values is not None
    stored_values['title'] = 'Inserted concurrently'
    memory_session.execute(delete(TableEpisodes))
    memory_session.commit()

    def fetch(*, apikey_sonarr: str | None, series_id: int) -> list[Episode]:
        memory_session.add(TableEpisodes(**stored_values))
        memory_session.flush()
        return records

    monkeypatch.setattr(episodes, 'get_episodes_from_sonarr_api', fetch)
    sql_reads.clear()
    episodes.sync_episodes(7, defer_search=True)

    assert len(sql_reads) == 3
    assert memory_session.execute(select(TableEpisodes.title)).scalar_one() == 'Changed 1'


@pytest.mark.parametrize('stored_monitored', [True, False])
def test_episode_monitored_state_uses_loaded_rows(stored_monitored: bool, memory_session: Session,
                                                 monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_episodes(monkeypatch, memory_session, 1)
    records[0].monitored = False
    memory_session.execute(update(TableEpisodes).values(monitored=str(stored_monitored)))
    monkeypatch.setattr(episodes.settings.general, 'debug', False)
    monkeypatch.setattr(episodes.settings.sonarr, 'sync_only_monitored_series', True)
    monkeypatch.setattr(episodes.settings.sonarr, 'sync_only_monitored_episodes', True)
    sql_reads.clear()

    episodes.sync_episodes(7, defer_search=True)

    assert len(sql_reads) == 2
    expected_title = 'Changed 1' if stored_monitored else 'Pilot'
    assert memory_session.execute(select(TableEpisodes.title)).scalar_one() == expected_title


@pytest.mark.parametrize('changed', ['id', 'path', 'both'])
def test_movie_sync_preserves_concurrently_replaced_file(changed: str, memory_session: Session,
                                                       monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_movies(monkeypatch, memory_session, 2)
    file = records[1].movieFile
    assert file is not None
    new_id = file.id + 1 if changed in ('id', 'both') else file.id
    new_path = '/movies/replaced.mkv' if changed in ('path', 'both') else file.path
    emitted: list[int] = []

    def replace_next_file(*, type: str, action: str, payload: int) -> None:
        emitted.append(payload)
        memory_session.execute(update(TableMovies).where(TableMovies.radarrId == 2)
                               .values(movie_file_id=new_id, path=new_path, title='Concurrent update'))

    monkeypatch.setattr(movies, 'event_stream', replace_next_file)
    sql_reads.clear()

    movies.update_movies(job_id=1)

    assert len(sql_reads) == 1
    assert emitted == [1]
    stored = memory_session.execute(select(TableMovies.title, TableMovies.movie_file_id, TableMovies.path)
                                    .where(TableMovies.radarrId == 2)).one()
    assert tuple(stored) == ('Concurrent update', new_id, new_path)


@pytest.mark.parametrize('changed', ['id', 'path', 'both'])
def test_episode_sync_preserves_concurrently_replaced_file(changed: str, memory_session: Session,
                                                         monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    records = configure_episodes(monkeypatch, memory_session, 1)
    file = records[0].episodeFile
    assert file is not None
    new_id = file.id + 1 if changed in ('id', 'both') else file.id
    new_path = '/show/replaced.mkv' if changed in ('path', 'both') else file.path

    def replace_file(*, apikey_sonarr: str | None, series_id: int) -> list[Episode]:
        memory_session.execute(update(TableEpisodes).where(TableEpisodes.sonarrEpisodeId == 1)
                               .values(episode_file_id=new_id, path=new_path, title='Concurrent update'))
        return records

    monkeypatch.setattr(episodes, 'get_episodes_from_sonarr_api', replace_file)
    monkeypatch.setattr(episodes, 'event_stream', lambda **kwargs: pytest.fail('Stale episode update'))
    monkeypatch.setattr(episodes, '_is_there_missing_subtitles',
                        lambda **kwargs: pytest.fail('A stale update must not schedule a search'))
    sql_reads.clear()

    episodes.sync_episodes(7)

    assert len(sql_reads) == 2
    stored = memory_session.execute(select(TableEpisodes.title, TableEpisodes.episode_file_id, TableEpisodes.path)
                                    .where(TableEpisodes.sonarrEpisodeId == 1)).one()
    assert tuple(stored) == ('Concurrent update', new_id, new_path)
