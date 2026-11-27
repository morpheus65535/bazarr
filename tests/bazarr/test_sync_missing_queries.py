from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.database import TableEpisodes, TableFailedSubtitleAttempts, TableMissingSubtitles
from sonarr.sync import episodes
from subtitles import wanted_state
from tests.bazarr.test_sync_lookups import configure_episodes, sql_reads


@pytest.mark.parametrize('count', [1, 20, 205])
def test_sync_loads_due_episodes_once(count: int, memory_session: Session,
                                    monkeypatch: pytest.MonkeyPatch, sql_reads: list[str]) -> None:
    configure_episodes(monkeypatch, memory_session, count)
    monkeypatch.setattr(wanted_state, 'database', memory_session)
    monkeypatch.setattr(wanted_state, 'get_adaptive_search_policy', lambda: None)
    monkeypatch.setattr(episodes, 'get_exclusion_clause', lambda kind: [])
    monkeypatch.setattr(episodes.os.path, 'exists', lambda path: True)
    queued: list[int] = []
    monkeypatch.setattr(episodes, 'jobs_queue', SimpleNamespace(
        feed_jobs_pending_queue=lambda **kwargs: queued.append(kwargs['kwargs']['no'])))
    memory_session.add_all([TableMissingSubtitles(media_type='series', media_id=identifier, language='en')
                            for identifier in range(1, count + 1)])
    memory_session.flush()
    sql_reads.clear()

    episodes.sync_episodes(7)

    assert len(sql_reads) == 4
    assert queued == list(range(1, count + 1))


def test_due_episode_lookup_preserves_exclusions_and_retry_windows(memory_session: Session,
                                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    configure_episodes(monkeypatch, memory_session, 3)
    monkeypatch.setattr(wanted_state, 'database', memory_session)
    monkeypatch.setattr(episodes, 'get_exclusion_clause', lambda kind: [TableEpisodes.sonarrEpisodeId != 2])
    now = datetime.now().timestamp()
    monkeypatch.setattr(wanted_state, 'get_adaptive_search_policy', lambda: {
        'initial_search_cutoff': now - timedelta(days=21).total_seconds(),
        'latest_search_cutoff': now - timedelta(days=7).total_seconds(),
    })
    memory_session.add_all([TableMissingSubtitles(media_type='series', media_id=identifier, language='en')
                            for identifier in (1, 2, 3)])
    memory_session.add(TableFailedSubtitleAttempts(media_type='series', media_id=3, language='en',
                                                   initial_attempt_at=now - timedelta(days=30).total_seconds(),
                                                   latest_attempt_at=now))
    memory_session.flush()

    assert episodes._get_due_missing_episode_ids(series_id=7) == {1}
    assert episodes._is_there_missing_subtitles(episode_id=1)
    assert not episodes._is_there_missing_subtitles(episode_id=2)
    assert not episodes._is_there_missing_subtitles(episode_id=3)
    assert not episodes._is_there_missing_subtitles()
    assert not episodes._is_there_missing_subtitles(series_id=7, episode_id=1)


def test_sync_checks_missing_state_after_indexing(memory_session: Session,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    records = configure_episodes(monkeypatch, memory_session, 1)
    assert records[0].episodeFile is not None
    records[0].episodeFile.id += 1
    monkeypatch.setattr(wanted_state, 'database', memory_session)
    monkeypatch.setattr(wanted_state, 'get_adaptive_search_policy', lambda: None)
    monkeypatch.setattr(episodes, 'get_exclusion_clause', lambda kind: [])
    monkeypatch.setattr(episodes.os.path, 'exists', lambda path: True)
    queued: list[int] = []
    monkeypatch.setattr(episodes, 'jobs_queue', SimpleNamespace(
        feed_jobs_pending_queue=lambda **kwargs: queued.append(kwargs['kwargs']['no'])))

    def index(identifier: int) -> None:
        memory_session.add(TableMissingSubtitles(media_type='series', media_id=identifier, language='en'))
        memory_session.flush()

    monkeypatch.setattr(episodes, 'store_subtitles', index)
    episodes.sync_episodes(7)
    assert queued == [1]


def test_unchanged_sync_skips_missing_lookup(memory_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_episodes(monkeypatch, memory_session, 1)
    memory_session.execute(update(TableEpisodes).values(title='Changed 1'))
    monkeypatch.setattr(episodes, '_get_due_missing_episode_ids',
                        lambda **kwargs: pytest.fail('No episodes changed'))
    episodes.sync_episodes(7)
