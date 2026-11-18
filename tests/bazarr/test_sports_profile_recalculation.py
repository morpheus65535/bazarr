"""
Sports events follow the same recalculation rules as episodes and movies when a languages profile or a related
setting changes.

The profile tests run the settings endpoint and the sports indexer against the real models on SQLite, so the
wanted list is read back from the shared missing subtitles table.
"""
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import api.system.settings as settings_api
from app import config
from app import database as db
from subtitles import wanted_state
from subtitles.indexer import movies as movies_indexer
from subtitles.indexer import series as series_indexer
from subtitles.indexer import sports as sports_indexer


@pytest.fixture
def sports_session(tmp_path, monkeypatch):
    engine = create_engine(f'sqlite:///{tmp_path / "profiles.sqlite"}')
    db.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode='create_savepoint')
    for module in (settings_api, db, wanted_state, sports_indexer):
        monkeypatch.setattr(module, 'database', session)
    monkeypatch.setattr(settings_api, 'event_stream', lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_api, 'save_settings', lambda *args, **kwargs: None)
    monkeypatch.setattr(sports_indexer, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(sports_indexer, 'get_language_equals', lambda: [])
    monkeypatch.setattr(settings_api.settings.general, 'use_sonarr', False)
    monkeypatch.setattr(settings_api.settings.general, 'use_radarr', False)
    db.update_profile_id_list.invalidate()
    try:
        yield session
    finally:
        db.update_profile_id_list.invalidate()
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def _item(item_id, language):
    return {"id": item_id, "language": language, "hi": "False", "forced": "False",
            "audio_exclude": "False", "audio_only_include": "False"}


def _profile(operator):
    return {
        "profileId": 9, "name": "Sports", "cutoff": None, "profileType": "enhanced",
        "items": {"groups": [{"id": 1, "operator": operator, "items": [_item(1, "en"), _item(2, "fr")]}]},
        "mustContain": [], "mustNotContain": [], "originalFormat": None, "tag": None,
    }


def _add_event_with_english_subtitle(session):
    # The league points at the profile, so the profile row comes first.
    profile = _profile("OR")
    session.execute(db.insert(db.TableLanguagesProfiles).values(
        profileId=9, name='Sports', items=json.dumps(profile['items']), mustContain='[]', mustNotContain='[]',
        profileType='enhanced'))
    session.execute(db.insert(db.TableSportsLeagues).values(
        sportarrLeagueId=1, title='League 1', path='/sports/1', profileId=9, tags='[]', monitored='True'))
    session.execute(db.insert(db.TableSportsEvents).values(
        id=1, sportarrLeagueId=1, sportarrEventId=10, partNumber=0, path='/sports/1/10.mkv', title='Event 10',
        season=2026, episode=1, monitored='True', file_id=100, audio_language='[]',
        missing_subtitles_calculated=False))
    session.execute(db.insert(db.TableSportsEventsSubtitles).values(
        sportsEventId=1, sportarrLeagueId=1, language='en', forced=False, hi=False, path='/sports/1/10.en.srt'))


def _sports_wanted(session):
    return session.execute(
        db.select(db.TableMissingSubtitles.media_id, db.TableMissingSubtitles.language)
        .where(db.TableMissingSubtitles.media_type == 'sports')).all()


def _post_profiles(client, api_key, profiles):
    return client.post("/api/system/settings", data={"languages-profiles": json.dumps(profiles)},
                       headers={"X-API-KEY": api_key})


def test_switching_a_profile_group_from_or_to_and_updates_the_sports_wanted_list(
        sports_session, api_client, api_key, monkeypatch):
    monkeypatch.setattr(settings_api.settings.general, 'use_sportarr', True)
    _add_event_with_english_subtitle(sports_session)

    assert _post_profiles(api_client, api_key, [_profile("OR")]).status_code == 204
    # One language of an OR group is enough.
    assert _sports_wanted(sports_session) == []
    assert sports_session.execute(db.select(db.TableSportsEvents.missing_subtitles_calculated)).scalar_one()

    assert _post_profiles(api_client, api_key, [_profile("AND")]).status_code == 204
    # An AND group needs every language.
    assert _sports_wanted(sports_session) == [(1, 'fr')]


def test_saving_profiles_leaves_sports_alone_when_sportarr_is_disabled(
        sports_session, api_client, api_key, monkeypatch):
    monkeypatch.setattr(settings_api.settings.general, 'use_sportarr', False)
    calls = []
    monkeypatch.setattr(settings_api, 'list_missing_subtitles_sports', lambda *args, **kwargs: calls.append(args))

    assert _post_profiles(api_client, api_key, [_profile("AND")]).status_code == 204

    assert calls == []


@pytest.mark.parametrize('use_sportarr', [True, False], ids=['sportarr-enabled', 'sportarr-disabled'])
def test_code3_profile_fix_recalculates_sports_with_series_and_movies(sports_session, monkeypatch, use_sportarr):
    sports_session.execute(db.insert(db.TableLanguagesProfiles).values(
        profileId=3, name='Basic', items=json.dumps([_item(1, 'eng')]), mustContain='[]', mustNotContain='[]',
        profileType=db.PROFILE_TYPE_BASIC))
    from languages import get_languages

    calls = []
    monkeypatch.setattr(get_languages, 'alpha2_from_alpha3', lambda code: 'en')
    monkeypatch.setattr(db.settings.general, 'use_sportarr', use_sportarr)
    monkeypatch.setattr(series_indexer, 'list_missing_subtitles', lambda: calls.append('series'))
    monkeypatch.setattr(movies_indexer, 'list_missing_subtitles_movies', lambda: calls.append('movies'))
    monkeypatch.setattr(sports_indexer, 'list_missing_subtitles_sports', lambda: calls.append('sports'))

    db.fix_code3_languages_in_languages_profiles()

    assert calls == (['sports'] if use_sportarr else [])


@pytest.fixture
def queued(monkeypatch):
    from app.jobs_queue import jobs_queue

    jobs = []
    monkeypatch.setattr(jobs_queue, 'feed_jobs_pending_queue', lambda **kwargs: jobs.append(kwargs))
    monkeypatch.setattr(config, 'write_config', lambda: None)
    monkeypatch.setattr(db, 'database', type('Database', (), {'execute': lambda self, statement: None})())
    monkeypatch.setattr(config.settings.general, 'use_sonarr', False)
    monkeypatch.setattr(config.settings.general, 'use_radarr', False)
    return jobs


@pytest.mark.parametrize('key, value, func, kwargs', [
    ('use_embedded_subs', 'false', 'list_missing_subtitles_sports', {}),
    ('language_equals', [''], 'list_missing_subtitles_sports', {}),
    ('default_und_audio_lang', 'en', 'list_missing_subtitles_sports', {}),
    ('default_und_embedded_subtitles_lang', 'en', 'sports_full_scan_subtitles', {'use_cache': True}),
])
@pytest.mark.parametrize('use_sportarr', [True, False], ids=['sportarr-enabled', 'sportarr-disabled'])
def test_subtitle_setting_changes_queue_sports(queued, monkeypatch, key, value, func, kwargs, use_sportarr):
    # Saving changes the real setting, so the current value is restored after the test.
    monkeypatch.setattr(config.settings.general, key, getattr(config.settings.general, key))
    monkeypatch.setattr(config.settings.general, 'use_sportarr', use_sportarr)

    config.save_settings([(f'settings-general-{key}', value if isinstance(value, list) else [value])])

    sports_jobs = [(job['module'], job['func'], job['kwargs']) for job in queued
                   if job['module'] == 'subtitles.indexer.sports']
    assert sports_jobs == ([('subtitles.indexer.sports', func, kwargs)] if use_sportarr else [])
