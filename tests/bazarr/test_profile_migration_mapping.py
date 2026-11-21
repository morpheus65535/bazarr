# coding=utf-8
"""Tests for the basic to enhanced profile conversion in bazarr/app/profile_migration.py."""
import pytest

import api.system.settings as settings_api
from app.profile_migration import convert_basic_profile


def _item(item_id, language='en', **overrides):
    item = {'id': item_id, 'language': language, 'forced': 'False', 'hi': 'False',
            'audio_exclude': 'False', 'audio_only_include': 'False'}
    item.update(overrides)
    return item


def _group_ids(result):
    return [group['id'] for group in result['groups']]


def _group_languages(result):
    return [(group['id'], group['operator'], [item['language'] for item in group['items']])
            for group in result['groups']]


def _as_enhanced_profile(result, cutoff):
    return {'name': 'converted', 'profileType': 'enhanced', 'items': result, 'cutoff': cutoff}


def test_each_item_becomes_its_own_and_group():
    result, cutoff = convert_basic_profile([_item(1, 'en'), _item(2, 'fr')], None)

    assert _group_languages(result) == [(1, 'AND', ['en']), (2, 'AND', ['fr'])]
    assert [group['items'][0]['id'] for group in result['groups']] == [1, 2]
    assert cutoff is None


@pytest.mark.parametrize('ids, cutoff, expected_cutoff', [
    pytest.param([5, 9], 9, 2, id='cutoff-on-second-item'),
    pytest.param([5, 9], 5, 1, id='cutoff-on-first-item'),
    pytest.param([7, 3, 4], 4, 3, id='cutoff-keeps-list-order-not-id-order'),
])
def test_ids_are_renumbered_and_cutoff_remapped(ids, cutoff, expected_cutoff):
    items = [_item(item_id, language) for item_id, language in zip(ids, ['en', 'fr', 'de'])]

    result, new_cutoff = convert_basic_profile(items, cutoff)

    assert [group['items'][0]['id'] for group in result['groups']] == [1, 2, 3][:len(ids)]
    assert _group_ids(result) == [1, 2, 3][:len(ids)]
    assert new_cutoff == expected_cutoff


def test_duplicate_item_ids_are_renumbered_and_cutoff_follows_first_match():
    # get_profile_cutoff() returns the first item with the id, so the cutoff must follow that item.
    result, cutoff = convert_basic_profile([_item(1, 'en'), _item(1, 'fr'), _item(2, 'de')], 1)

    assert _group_languages(result) == [(1, 'AND', ['en']), (2, 'AND', ['fr']), (3, 'AND', ['de'])]
    assert cutoff == 1


def test_cutoff_on_second_of_duplicate_ids_is_not_used():
    # Only the first item with the id is the cutoff, the same as in the basic evaluator.
    result, cutoff = convert_basic_profile([_item(1, 'en'), _item(1, 'fr')], 1)

    assert cutoff == 1
    assert result['groups'][0]['items'][0]['language'] == 'en'


@pytest.mark.parametrize('cutoff', [None, 0], ids=['none', 'zero'])
def test_unset_cutoff_stays_unset(cutoff):
    _, new_cutoff = convert_basic_profile([_item(1)], cutoff)

    assert new_cutoff is None


def test_any_cutoff_is_kept():
    _, new_cutoff = convert_basic_profile([_item(1), _item(2, 'fr')], 65535)

    assert new_cutoff == 65535


def test_cutoff_matching_no_item_becomes_unset():
    _, new_cutoff = convert_basic_profile([_item(1), _item(2, 'fr')], 99)

    assert new_cutoff is None


def test_cutoff_matching_item_without_language_becomes_unset():
    # The basic evaluator cannot use an item without a language code, so the cutoff is never met.
    items = [{'id': 4, 'forced': 'False', 'hi': 'False'}, _item(1, 'fr')]

    _, new_cutoff = convert_basic_profile(items, 4)

    assert new_cutoff is None


def test_items_without_language_are_dropped():
    items = ['not-an-item', {'id': 2, 'language': ''}, _item(3, 'fr')]

    result, _ = convert_basic_profile(items, None)

    assert _group_languages(result) == [(1, 'AND', ['fr'])]


def test_profile_without_any_language_cannot_be_converted():
    with pytest.raises(ValueError):
        convert_basic_profile([{'id': 1, 'forced': 'False'}], None)

    with pytest.raises(ValueError):
        convert_basic_profile([], None)


def test_missing_audio_flags_are_filled_with_false():
    result, _ = convert_basic_profile([{'id': 1, 'language': 'en', 'forced': 'False', 'hi': 'False'}], None)

    item = result['groups'][0]['items'][0]
    assert item['audio_exclude'] == 'False'
    assert item['audio_only_include'] == 'False'


@pytest.mark.parametrize('raw, expected', [
    pytest.param(True, 'True', id='bool-true'),
    pytest.param(False, 'False', id='bool-false'),
    pytest.param('True', 'True', id='string-true'),
    pytest.param('False', 'False', id='string-false'),
])
def test_forced_and_audio_flags_are_normalized_to_strings(raw, expected):
    item = _item(1, forced=raw, audio_exclude=raw, audio_only_include=raw)

    result, _ = convert_basic_profile([item], None)

    converted = result['groups'][0]['items'][0]
    assert (converted['forced'], converted['audio_exclude'], converted['audio_only_include']) == (
        expected, expected, expected)


@pytest.mark.parametrize('raw, expected', [
    pytest.param('True', 'True', id='hi'),
    pytest.param('False', 'False', id='normal'),
    pytest.param('Excluded', 'Excluded', id='non-hi'),
    pytest.param(True, 'True', id='bool-hi'),
])
def test_hi_values_are_normalized(raw, expected):
    result, _ = convert_basic_profile([_item(1, hi=raw)], None)

    assert result['groups'][0]['items'][0]['hi'] == expected


def test_audio_options_and_other_item_keys_are_kept():
    item = _item(1, 'en', audio_exclude='True', audio_only_include='False', custom_key='kept')

    result, _ = convert_basic_profile([item], None)

    converted = result['groups'][0]['items'][0]
    assert converted['audio_exclude'] == 'True'
    assert converted['custom_key'] == 'kept'


def test_input_items_are_not_modified():
    item = _item(3, 'en', forced=True)
    original = dict(item)

    convert_basic_profile([item], 3)

    assert item == original


@pytest.mark.parametrize('items, cutoff', [
    pytest.param([_item(1, 'en'), _item(2, 'fr', hi='Excluded')], 1, id='two-items-cutoff-first'),
    pytest.param([_item(1, 'en'), _item(2, 'en', hi='True')], 2, id='same-language-hi-cutoff'),
    pytest.param([_item(4, 'en', audio_only_include='True'), _item(5, 'fr')], 4, id='audio-only-cutoff'),
    pytest.param([_item(1, 'en', audio_exclude='True')], 65535, id='any-cutoff'),
    pytest.param([_item(1, 'en'), _item(1, 'fr')], 1, id='duplicate-ids'),
    pytest.param([_item(1, 'en'), _item(2, 'fr')], 99, id='unknown-cutoff'),
])
def test_converted_profiles_pass_the_enhanced_profile_validator(items, cutoff):
    result, new_cutoff = convert_basic_profile(items, cutoff)

    assert settings_api.validate_languages_profiles([_as_enhanced_profile(result, new_cutoff)]) is None
