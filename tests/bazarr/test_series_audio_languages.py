from flask.testing import FlaskClient
from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from api import utils
from app.database import TableEpisodes, TableShows


def add_series(session: Session, series_id: int, audio_language: str | None = '[]') -> None:
    session.add(TableShows(sonarrSeriesId=series_id, path=f'/series/{series_id}',
                          title=f'Series {series_id}', sortTitle=f'Series {series_id}',
                          audio_language=audio_language))
    session.flush()


def add_episode(session: Session, episode_id: int, series_id: int, languages: str | None) -> None:
    session.add(TableEpisodes(sonarrEpisodeId=episode_id, sonarrSeriesId=series_id,
                             season=1, episode=episode_id, title='Episode',
                             path=f'/series/{series_id}/{episode_id}.mkv', audio_language=languages))


def test_repeated_episode_languages_are_parsed_once(
    memory_session: Session, monkeypatch: MonkeyPatch, mocker: MockerFixture,
) -> None:
    monkeypatch.setattr(utils, 'database', memory_session)
    for series_id in (1, 2):
        add_series(memory_session, series_id)
    for episode_id in range(1, 1001):
        add_episode(memory_session, episode_id, episode_id % 2 + 1,
                    "['English']" if episode_id % 3 else "['English', 'French']")
    memory_session.commit()
    parse = mocker.spy(utils, 'parse_text_list_or_default')
    execute = mocker.spy(memory_session, 'execute')

    result = utils.get_series_audio_languages([1, 2])

    assert {series_id: set(names) for series_id, names in result.items()} == {
        1: {'English', 'French'}, 2: {'English', 'French'},
    }
    assert parse.call_count == 2
    assert execute.call_count == 1


def test_empty_request_does_not_query(memory_session: Session, monkeypatch: MonkeyPatch,
                                     mocker: MockerFixture) -> None:
    monkeypatch.setattr(utils, 'database', memory_session)
    execute = mocker.spy(memory_session, 'execute')

    assert utils.get_series_audio_languages([]) == {}
    execute.assert_not_called()


def test_invalid_and_empty_languages(memory_session: Session, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(utils, 'database', memory_session)
    for series_id in (1, 2):
        add_series(memory_session, series_id)
    for episode_id, languages in enumerate((None, '[]', '[', "['English', None, '']"), 1):
        add_episode(memory_session, episode_id, 1, languages)
    memory_session.commit()

    result = utils.get_series_audio_languages([1, 2])

    assert set(result[1]) == {'English', None, ''}
    assert result[2] == []


def test_query_batches_large_series_lists(memory_session: Session, monkeypatch: MonkeyPatch,
                                         mocker: MockerFixture) -> None:
    monkeypatch.setattr(utils, 'database', memory_session)
    add_series(memory_session, 901)
    add_episode(memory_session, 1, 901, "['French']")
    memory_session.commit()
    execute = mocker.spy(memory_session, 'execute')

    result = utils.get_series_audio_languages(list(range(1, 902)))

    assert result[901] == ['French']
    assert result[1] == []
    assert execute.call_count == 2


def test_next_request_observes_episode_updates(memory_session: Session, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(utils, 'database', memory_session)
    add_series(memory_session, 1)
    add_episode(memory_session, 1, 1, "['English']")
    memory_session.commit()
    assert utils.get_series_audio_languages([1]) == {1: ['English']}

    episode = memory_session.get(TableEpisodes, 1)
    assert episode is not None
    episode.audio_language = "['French']"
    memory_session.commit()

    assert utils.get_series_audio_languages([1]) == {1: ['French']}


def test_series_list_batches_only_returned_fallbacks(
    api_client: FlaskClient, api_key: str, memory_session: Session,
    monkeypatch: MonkeyPatch, mocker: MockerFixture,
) -> None:
    from api.series import series

    monkeypatch.setattr(series, 'database', memory_session)
    monkeypatch.setattr(utils, 'database', memory_session)
    mocker.patch.object(utils, 'get_subtitles', return_value=[])
    for series_id, language in ((1, '[]'), (2, "['Dutch']"), (3, '[]')):
        add_series(memory_session, series_id, language)
        add_episode(memory_session, series_id, series_id, "['English']")
    memory_session.commit()
    aggregate = mocker.spy(series, 'get_series_audio_languages')
    parse = mocker.spy(utils, 'parse_text_list_or_default')

    response = api_client.get('/api/series?length=2', headers={'X-API-KEY': api_key})

    assert response.status_code == 200
    assert response.json is not None
    assert response.json['total'] == 3
    assert [row['audio_language'][0]['name'] for row in response.json['data']] == ['English', 'Dutch']
    aggregate.assert_called_once_with([1])
    parse.assert_called_once_with("['English']")


def test_single_series_fallback_keeps_undefined_language_default(
    memory_session: Session, monkeypatch: MonkeyPatch, mocker: MockerFixture,
) -> None:
    monkeypatch.setattr(utils, 'database', memory_session)
    monkeypatch.setattr(utils.settings.general, 'default_und_audio_lang', 'en')
    mocker.patch.object(utils, 'get_subtitles', return_value=[])
    add_series(memory_session, 1)
    add_episode(memory_session, 1, 1, '[None]')
    memory_session.commit()

    result = utils.postprocess({'sonarrSeriesId': 1, 'audio_language': '[]'})

    assert result['audio_language'] == [{'name': 'English', 'code2': 'en', 'code3': 'eng'}]
