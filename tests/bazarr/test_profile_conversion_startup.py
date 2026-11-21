# coding=utf-8
"""Tests for the startup conversion of basic languages profiles to enhanced profiles."""
import json

import pytest
from sqlalchemy import insert

import api.system.settings as settings_api
import app.database as app_database
from app.database import TableLanguagesProfiles, convert_basic_languages_profiles_to_enhanced, select


def _item(item_id, language, **overrides):
    item = {'id': item_id, 'language': language, 'forced': 'False', 'hi': 'False',
            'audio_exclude': 'False', 'audio_only_include': 'False'}
    item.update(overrides)
    return item


def _insert(session, profile_id, name, items, cutoff=None, profile_type='basic', **extra):
    session.execute(insert(TableLanguagesProfiles).values(
        profileId=profile_id, name=name, cutoff=cutoff, items=items, mustContain=extra.get('mustContain', '[]'),
        mustNotContain=extra.get('mustNotContain', '[]'), originalFormat=None, tag=extra.get('tag'),
        profileType=profile_type))
    session.commit()


def _row(session, profile_id):
    return session.execute(
        select(TableLanguagesProfiles).where(TableLanguagesProfiles.profileId == profile_id)).scalar_one()


@pytest.fixture
def profiles_db(memory_session, monkeypatch):
    monkeypatch.setattr(app_database, 'database', memory_session)
    return memory_session


def test_basic_profiles_are_converted_and_keep_their_identity(profiles_db):
    _insert(profiles_db, 1, 'English', json.dumps([_item(1, 'en'), _item(2, 'fr')]), cutoff=2,
            tag='movies', mustContain="['hearing']", mustNotContain="['sdh']")

    convert_basic_languages_profiles_to_enhanced()

    row = _row(profiles_db, 1)
    assert row.profileType == 'enhanced'
    assert (row.profileId, row.name, row.tag, row.mustContain, row.mustNotContain) == (
        1, 'English', 'movies', "['hearing']", "['sdh']")
    assert json.loads(row.items) == {'groups': [
        {'id': 1, 'operator': 'AND', 'items': [_item(1, 'en')]},
        {'id': 2, 'operator': 'AND', 'items': [_item(2, 'fr')]},
    ]}
    assert row.cutoff == 2


def test_converted_profiles_pass_the_enhanced_validator(profiles_db):
    items = json.dumps([_item(1, 'en', hi='Excluded'), _item(2, 'fr', forced='True')])
    _insert(profiles_db, 1, 'Mixed', items, cutoff=65535)

    convert_basic_languages_profiles_to_enhanced()

    row = _row(profiles_db, 1)
    profile = {'name': row.name, 'profileType': row.profileType, 'cutoff': row.cutoff,
               'items': json.loads(row.items)}
    assert settings_api.validate_languages_profiles([profile]) is None


def test_second_run_changes_nothing(profiles_db):
    _insert(profiles_db, 1, 'English', json.dumps([_item(1, 'en'), _item(2, 'fr')]), cutoff=1)
    convert_basic_languages_profiles_to_enhanced()
    before = _row(profiles_db, 1)

    convert_basic_languages_profiles_to_enhanced()

    after = _row(profiles_db, 1)
    assert (after.items, after.cutoff, after.profileType) == (before.items, before.cutoff, before.profileType)


def test_enhanced_profiles_are_left_untouched(profiles_db):
    stored = json.dumps({'groups': [{'id': 7, 'operator': 'OR', 'items': [_item(9, 'de')]}]})
    _insert(profiles_db, 2, 'Already enhanced', stored, cutoff=7, profile_type='enhanced')

    convert_basic_languages_profiles_to_enhanced()

    row = _row(profiles_db, 2)
    assert (row.items, row.cutoff, row.profileType) == (stored, 7, 'enhanced')


@pytest.mark.parametrize('items', [
    pytest.param('[]', id='no-items'),
    pytest.param('[{"id": 1, "forced": "False"}]', id='no-language'),
    pytest.param('{"groups": []}', id='not-a-list'),
    pytest.param('not json', id='invalid-json'),
], )
def test_profile_that_cannot_be_converted_stays_basic(profiles_db, items):
    _insert(profiles_db, 3, 'Broken', items, cutoff=1)

    convert_basic_languages_profiles_to_enhanced()

    row = _row(profiles_db, 3)
    assert (row.profileType, row.items, row.cutoff) == ('basic', items, 1)


def test_unconvertible_profile_does_not_block_other_profiles(profiles_db):
    _insert(profiles_db, 3, 'Broken', '[]')
    _insert(profiles_db, 4, 'Good', json.dumps([_item(1, 'en')]))

    convert_basic_languages_profiles_to_enhanced()

    assert _row(profiles_db, 3).profileType == 'basic'
    assert _row(profiles_db, 4).profileType == 'enhanced'


def test_cutoff_is_remapped_to_the_group_of_the_basic_cutoff_item(profiles_db):
    _insert(profiles_db, 5, 'Remap', json.dumps([_item(1, 'en'), _item(1, 'fr'), _item(2, 'de')]), cutoff=1)

    convert_basic_languages_profiles_to_enhanced()

    row = _row(profiles_db, 5)
    groups = json.loads(row.items)['groups']
    assert row.cutoff == 1
    assert [group['items'][0]['language'] for group in groups] == ['en', 'fr', 'de']


def test_empty_table_is_a_no_op(profiles_db):
    convert_basic_languages_profiles_to_enhanced()

    assert profiles_db.execute(select(TableLanguagesProfiles)).all() == []
