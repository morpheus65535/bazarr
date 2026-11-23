# coding=utf-8
"""
Consumers of converted languages profiles: desired languages, flat items, cutoff items, health issues and the API.

Each view is read before and after the startup conversion from the same library as the golden snapshot. Apart from the
cutoff and item ids, which the conversion renumbers, the views must match.
"""
import json
from types import SimpleNamespace

import pytest

import api.system.settings as settings_api
import app.database as app_database
from app.database import TableLanguagesProfiles, convert_basic_languages_profiles_to_enhanced, select
from tests.bazarr.test_profile_conversion_golden import LIBRARY_PROFILES, insert_library

ITEM_FIELDS = ('language', 'hi', 'forced', 'audio_exclude', 'audio_only_include')
META_FIELDS = ('name', 'tag', 'originalFormat', 'mustContain', 'mustNotContain')


def _essence(item):
    """The fields that decide what a consumer does with an item, without the id."""
    return tuple(item[field] for field in ITEM_FIELDS)


def _view(profile_id):
    profile = app_database.get_profiles_list(profile_id=profile_id)
    return {
        'desired': app_database.get_desired_languages(profile_id),
        'items': [_essence(item) for item in profile['items']],
        'meta': {field: profile.get(field) for field in META_FIELDS},
        'cutoff_items': [_essence(item) for item in app_database.get_profile_cutoff(profile_id) or []],
    }


def _expected_before(profile_id):
    """The view a basic profile gave before the conversion, computed from the stored items of the library."""
    name, cutoff, items = LIBRARY_PROFILES[profile_id]
    if cutoff == 65535:
        cutoff_items = items
    elif cutoff:
        first_match = next((item for item in items if item['id'] == cutoff), None)
        cutoff_items = [first_match] if first_match else None
    else:
        cutoff_items = None
    return {
        'desired': [item['language'] for item in items],
        'items': [_essence(item) for item in items],
        'meta': {'name': name, 'tag': f'tag-{profile_id}' if profile_id == 2 else None, 'originalFormat': None,
                 'mustContain': [], 'mustNotContain': []},
        'cutoff_items': [_essence(item) for item in cutoff_items or []],
    }


@pytest.fixture
def views_before_and_after(memory_session, monkeypatch):
    monkeypatch.setattr(app_database, 'database', memory_session)
    insert_library(memory_session)
    before = {profile_id: _expected_before(profile_id) for profile_id in LIBRARY_PROFILES}

    convert_basic_languages_profiles_to_enhanced()
    app_database.update_profile_id_list.invalidate()
    after = {profile_id: _view(profile_id) for profile_id in LIBRARY_PROFILES}
    return before, after


@pytest.mark.parametrize('profile_id', list(LIBRARY_PROFILES))
def test_desired_languages_and_items_are_unchanged(views_before_and_after, profile_id):
    before, after = views_before_and_after

    assert after[profile_id]['desired'] == before[profile_id]['desired']
    assert after[profile_id]['items'] == before[profile_id]['items']


@pytest.mark.parametrize('profile_id', list(LIBRARY_PROFILES))
def test_profile_metadata_is_unchanged(views_before_and_after, profile_id):
    before, after = views_before_and_after

    assert after[profile_id]['meta'] == before[profile_id]['meta']


@pytest.mark.parametrize('profile_id', list(LIBRARY_PROFILES))
def test_cutoff_items_are_unchanged(views_before_and_after, profile_id):
    before, after = views_before_and_after

    assert after[profile_id]['cutoff_items'] == before[profile_id]['cutoff_items']


def test_api_lists_converted_profiles_as_enhanced(memory_session, monkeypatch, api_client, api_key):
    monkeypatch.setattr(app_database, 'database', memory_session)
    insert_library(memory_session)
    convert_basic_languages_profiles_to_enhanced()

    response = api_client.get('/api/system/languages/profiles', headers={'X-API-KEY': api_key})

    assert response.status_code == 200
    profiles = {profile['profileId']: profile for profile in response.get_json()}
    assert set(profiles) == set(LIBRARY_PROFILES)
    assert {profile['profileType'] for profile in profiles.values()} == {'enhanced'}
    assert all(profile['groups'] for profile in profiles.values())


def test_api_round_trip_of_converted_profiles_is_accepted_and_stored_unchanged(
        memory_session, monkeypatch, api_client, api_key):
    monkeypatch.setattr(app_database, 'database', memory_session)
    monkeypatch.setattr(settings_api, 'database', memory_session)
    monkeypatch.setattr(settings_api, 'event_stream', lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_api, 'list_missing_subtitles', lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_api, 'list_missing_subtitles_movies', lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_api, 'save_settings', lambda *args, **kwargs: None)
    insert_library(memory_session)
    convert_basic_languages_profiles_to_enhanced()
    stored_before = {row.profileId: (row.items, row.cutoff, row.profileType) for row in
                     memory_session.execute(select(TableLanguagesProfiles)).scalars()}

    listed = api_client.get('/api/system/languages/profiles', headers={'X-API-KEY': api_key}).get_json()
    # The settings page sends enhanced profiles with their groups, not the flat item list the GET returns.
    submission = [{
        'profileId': profile['profileId'], 'name': profile['name'], 'tag': profile['tag'],
        'profileType': profile['profileType'], 'cutoff': profile['cutoff'],
        'items': {'groups': profile['groups']},
        'mustContain': profile['mustContain'], 'mustNotContain': profile['mustNotContain'],
        'originalFormat': profile['originalFormat'],
    } for profile in listed]

    response = api_client.post('/api/system/settings', headers={'X-API-KEY': api_key},
                               data={'languages-profiles': json.dumps(submission), 'languages-enabled': ['en']})

    assert response.status_code == 204, response.get_data(as_text=True)
    stored_after = {row.profileId: (row.items, row.cutoff, row.profileType) for row in
                    memory_session.execute(select(TableLanguagesProfiles)).scalars()}
    assert stored_after == stored_before
