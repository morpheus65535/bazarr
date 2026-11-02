"""
Search order and profile options for the subtitle search, with the provider calls faked.

Covers the order languages are searched in (the profile priority), the skip of alternatives that a satisfied OR group
no longer needs, and that enhanced profiles drive the same per-language options as basic ones.
"""
from unittest import mock

import pytest

from subtitles.download import generate_subtitles, parse_language_object, _get_language_obj


def _item(item_id, language, hi='False', forced='False'):
    return {'id': item_id, 'language': language, 'hi': hi, 'forced': forced,
            'audio_exclude': 'False', 'audio_only_include': 'False'}


def _profile(items, groups=None, original_format=False, must_contain=None):
    profile = {'profileId': 1, 'name': 'test', 'cutoff': None, 'items': items,
               'mustContain': must_contain or [], 'mustNotContain': [], 'originalFormat': original_format, 'tag': None}
    if groups is not None:
        profile.update(profileType='enhanced', groups=groups)
    return profile


def _run_search(profile, languages, reload_side_effect=None, on_download=None):
    """Run generate_subtitles and return what was searched: [(language, hearing_impaired, kwargs), ...]."""
    video = mock.MagicMock()
    video.original_path = '/media/tv/Show/S01E01.mkv'

    settings = mock.MagicMock()
    settings.general.utf8_encode = False
    settings.embeddedsubtitles.prefer_embedded = False
    settings.translator.translate_fallback_enabled = False

    searched = []

    def fake_download(videos, languages, hearing_impaired, **kwargs):
        language = next(iter(languages))
        searched.append((parse_language_object(language), hearing_impaired, kwargs))
        if on_download:
            on_download(language)
        return {}

    reload = mock.MagicMock(side_effect=reload_side_effect) if reload_side_effect else mock.MagicMock(return_value=[])

    with mock.patch('subtitles.download.settings', settings), \
         mock.patch('subtitles.download.get_profiles_list', return_value=profile), \
         mock.patch('subtitles.download._get_pool') as pool, \
         mock.patch('subtitles.download._set_forced_providers'), \
         mock.patch('subtitles.download._get_scores', return_value=(0, 100, {})), \
         mock.patch('subtitles.download.get_video', return_value=video), \
         mock.patch('subtitles.download.download_best_subtitles', side_effect=fake_download), \
         mock.patch('subtitles.download.reload_missing_languages_from_db', reload), \
         mock.patch('subtitles.download.subliminal'):
        pool.return_value.providers = ['someprovider']
        list(generate_subtitles('/media/tv/Show/S01E01.mkv', languages, 'English', None, 'Show', 'series', 1,
                                check_if_still_required=reload_side_effect is not None))
    return searched


def test_languages_are_searched_in_the_given_priority_order():
    # Not alphabetical and not set order: the input order is the profile priority.
    languages = [('sv', 'False', 'False'), ('pl', 'False', 'False'), ('de', 'False', 'False'),
                 ('en', 'False', 'True'), ('it', 'False', 'False'), ('nl', 'False', 'False'),
                 ('es', 'False', 'False'), ('fr', 'False', 'False')]
    profile = _profile([_item(1, 'sv'), _item(2, 'pl'), _item(3, 'de'), _item(4, 'en', forced='True'),
                        _item(5, 'it'), _item(6, 'nl'), _item(7, 'es'), _item(8, 'fr')])

    searched = _run_search(profile, languages)

    assert [language for language, _, _ in searched] == [
        'sv', 'pl', 'de', 'en:forced', 'it', 'nl', 'es', 'fr',
    ]


def test_enhanced_profile_is_searched_in_group_priority_order():
    groups = [
        {'id': 1, 'operator': 'AND', 'items': [_item(1, 'en'), _item(2, 'fr')]},
        {'id': 2, 'operator': 'OR', 'items': [_item(3, 'de'), _item(4, 'it')]},
    ]
    languages = [('en', 'False', 'False'), ('fr', 'False', 'False'), ('de', 'False', 'False'), ('it', 'False', 'False')]
    profile = _profile([item for group in groups for item in group['items']], groups=groups)

    searched = _run_search(profile, languages)

    assert [language for language, _, _ in searched] == ['en', 'fr', 'de', 'it']


def test_alternative_is_not_searched_once_its_or_group_is_satisfied():
    # de and it are alternatives of one OR group. Once de is stored, the missing list no longer contains it.
    de, it, en = _get_language_obj([('de', 'False', 'False')])[0], _get_language_obj(
        [('it', 'False', 'False')])[0], _get_language_obj([('en', 'False', 'False')])[0]
    still_missing = [de, it, en]

    def reload_missing(path, media_type):
        return list(still_missing)

    def satisfy_or_group(language):
        if language == de:
            still_missing.remove(it)

    groups = [{'id': 2, 'operator': 'OR', 'items': [_item(3, 'de'), _item(4, 'it')]},
              {'id': 3, 'operator': 'AND', 'items': [_item(5, 'en')]}]
    profile = _profile([item for group in groups for item in group['items']], groups=groups)

    searched = _run_search(profile, [('de', 'False', 'False'), ('it', 'False', 'False'), ('en', 'False', 'False')],
                           reload_side_effect=reload_missing, on_download=satisfy_or_group)

    assert [language for language, _, _ in searched] == ['de', 'en']


@pytest.mark.parametrize('profile', [
    pytest.param(_profile([_item(1, 'en', hi='True')]), id='basic'),
    pytest.param(_profile([_item(1, 'en', hi='True')], groups=[
        {'id': 1, 'operator': 'OR', 'items': [_item(1, 'en', hi='True'), _item(2, 'fr')]}]), id='enhanced'),
])
def test_hi_item_forces_hi_search_for_basic_and_enhanced_profiles(profile):
    searched = _run_search(profile, [('en', 'True', 'False')])

    assert searched[0][1] == 'force HI'


def test_enhanced_profile_original_format_reaches_the_search():
    groups = [{'id': 1, 'operator': 'AND', 'items': [_item(1, 'en')]}]
    profile = _profile([_item(1, 'en')], groups=groups, original_format=True)

    searched = _run_search(profile, [('en', 'False', 'False')])

    assert searched[0][2]['use_original_format'] is True


def test_enhanced_profile_must_contain_reaches_the_release_filter():
    from subtitles.utils import get_ban_list

    groups = [{'id': 1, 'operator': 'AND', 'items': [_item(1, 'en')]}]
    profile = _profile([_item(1, 'en')], groups=groups, must_contain=['WEB'])

    with mock.patch('subtitles.utils.get_profiles_list', return_value=profile):
        ban_list = get_ban_list(1)

    assert ban_list == {'must_contain': ['WEB'], 'must_not_contain': []}
