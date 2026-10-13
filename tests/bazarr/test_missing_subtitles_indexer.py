# -*- coding: utf-8 -*-
"""
Tests for missing subtitles calculation in series and movies indexers.

This module tests the custom alpha2 code resolution fix for languages like
Spanish (Latino) with custom code "ea" that should map to standard Spanish.
"""
import ast
from types import SimpleNamespace

import pytest
from sqlalchemy.sql.dml import Update
from subliminal_patch import core

import app.database as app_database
from bazarr.languages.custom_lang import LatinAmericanSpanish, CustomLanguage
from subtitles.indexer import movies as movies_indexer
from subtitles.indexer import series as series_indexer


def test_custom_language_from_value_alpha2():
    """Test that CustomLanguage.from_value correctly finds custom languages by alpha2 code."""
    # Test Spanish (Latino) with alpha2 code 'ea'
    custom = CustomLanguage.from_value('ea', attr='alpha2')
    assert custom is not None
    assert custom.alpha2 == 'ea'
    assert custom.official_alpha3 == 'spa'  # Maps to Spanish

    # Test that from_value returns None for unknown codes
    custom = CustomLanguage.from_value('xx', attr='alpha2')
    assert custom is None


def test_custom_language_subzero_language():
    """Test that CustomLanguage.subzero_language() returns proper Language object."""
    custom = LatinAmericanSpanish()
    lang = custom.subzero_language()

    # Should return a Language object for Spanish
    assert lang.alpha3 == 'spa'
    assert 'es' in str(lang).lower() or 'spa' in str(lang).lower()


def test_language_parsing_with_custom_alpha2():
    """Test the language parsing logic that would be used in list_missing_subtitles."""
    # Test that we can find Spanish (Latino) by custom alpha2 code
    lang_code = 'ea'

    # This is the logic from the fixed code:
    custom = CustomLanguage.from_value(lang_code, "alpha2")
    if custom:
        lang_obj = custom.subzero_language()
        # Should get Spanish Language object
        assert lang_obj.alpha3 == 'spa'
    else:
        # Should not happen for 'ea'
        pytest.fail("Should have found LatinAmericanSpanish custom language")


def test_language_expansion_preserves_flags():
    """Test that forced and hi flags are preserved during language expansion."""
    # Test with Spanish (Latino) with forced flag
    lang_code = 'ea'
    forced = True
    hi = False

    custom = CustomLanguage.from_value(lang_code, "alpha2")
    assert custom is not None

    lang_obj = custom.subzero_language()
    # Assign flags (as done in the code)
    lang_obj.forced = forced
    lang_obj.hi = hi

    # Verify flags are preserved
    assert lang_obj.forced is True
    assert lang_obj.hi is False


def test_invalid_language_code_fallback():
    """Test that invalid language codes don't crash the system."""
    # Test with a code that's not recognized as custom
    lang_code = 'zz'

    custom = CustomLanguage.from_value(lang_code, "alpha2")
    # Should not find a custom language
    assert custom is None


def test_language_comparison_with_custom_alpha2():
    """Test that custom language expansion properly resolves to standard language alpha2."""
    # Simulate the actual comparison logic from list_missing_subtitles
    # When we have 'ea' (Spanish Latino), it should expand to 'es' (Spanish)

    lang_code = 'ea'
    custom = CustomLanguage.from_value(lang_code, "alpha2")
    assert custom is not None

    lang_obj = custom.subzero_language()
    assert lang_obj.alpha2 == 'es'  # Should resolve to standard Spanish


def test_custom_language_alpha2_resolution_in_conversion():
    """Test that custom alpha2 codes are converted back to proper alpha2 for comparison."""
    # This simulates the fix: when expanding actual subtitles with custom alpha2 codes
    # the code should resolve them to their standard alpha2 equivalents

    expanded_actual_subtitles_list = []

    # Simulate having a custom language 'ea' in the expanded set
    custom = CustomLanguage.from_value('ea', "alpha2")
    if custom:
        lang_obj = custom.subzero_language()
        lang_obj.forced = False
        lang_obj.hi = False

        # This is the fixed logic - use custom.alpha2 if custom else lang_obj.alpha2
        expanded_actual_subtitles_list.append({
            'language': custom.alpha2 if custom else lang_obj.alpha2,
            'forced': 'False',
            'hi': 'False'
        })

    # Verify the result
    assert len(expanded_actual_subtitles_list) == 1
    assert expanded_actual_subtitles_list[0]['language'] == 'ea'  # Still 'ea' as stored


def test_ietf_fallback_for_standard_languages():
    """Test that standard IETF language codes still work correctly."""
    # Test that 'es' (standard Spanish) still works
    lang_code = 'es'

    custom = CustomLanguage.from_value(lang_code, "alpha2")
    # Should not find a custom language for standard codes
    assert custom is None

    # Should parse with IETF
    lang_obj = core.Language.fromietf(lang_code)
    assert lang_obj.alpha2 == 'es'
    assert lang_obj.alpha3 == 'spa'


# Indexer tests below run the real list_missing_subtitles functions. Only database access is faked.

INDEXERS = [
    pytest.param(series_indexer, id='series'),
    pytest.param(movies_indexer, id='movies'),
]

ANY_CUTOFF = 65535

# Profile item types the UI can produce: the subtitle type selector maps to exactly these (forced, hi) pairs.
SUBTITLE_TYPES = {
    'normal': ('False', 'False'),
    'hi': ('False', 'True'),
    'non_hi': ('False', 'Excluded'),
    'forced': ('True', 'False'),
}

ACTUAL = {
    'none': [],
    'normal': [{'path': '/media/en.srt', 'code2': 'en', 'forced': False, 'hi': False}],
    'hi': [{'path': '/media/en.hi.srt', 'code2': 'en', 'forced': False, 'hi': True}],
    'forced': [{'path': '/media/en.forced.srt', 'code2': 'en', 'forced': True, 'hi': False}],
    'forced_hi': [{'path': '/media/en.forced.hi.srt', 'code2': 'en', 'forced': True, 'hi': True}],
}


def _profile_item(item_id, subtitle_type, language='en'):
    forced, hi = SUBTITLE_TYPES[subtitle_type]
    return {'id': item_id, 'language': language, 'forced': forced, 'hi': hi,
            'audio_exclude': 'False', 'audio_only_include': 'False'}


def _profile(items, cutoff=None):
    # Same key order as update_profile_id_list() because get_profile_cutoff() unpacks profile.values()
    return {'profileId': 1, 'name': 'test', 'cutoff': cutoff, 'items': items,
            'mustContain': [], 'mustNotContain': [], 'originalFormat': False, 'tag': None}


class _FakeDatabase:
    """Returns the single media row to the indexer and records the missing_subtitles value it writes."""

    def __init__(self, row):
        self.row = row
        self.missing = None

    def execute(self, statement):
        if isinstance(statement, Update):
            self.missing = ast.literal_eval(statement.compile().params['missing_subtitles'])
            return None
        return SimpleNamespace(all=lambda: [self.row])


def _missing(monkeypatch, indexer, profile, subtitles):
    """Run the indexer for one media item and return the sorted missing list it stored."""
    if indexer is series_indexer:
        row = SimpleNamespace(sonarrSeriesId=1, sonarrEpisodeId=1, profileId=1, audio_language='[]')
        run = indexer.list_missing_subtitles
    else:
        row = SimpleNamespace(radarrId=1, profileId=1, audio_language='[]')
        run = indexer.list_missing_subtitles_movies

    fake_database = _FakeDatabase(row)
    monkeypatch.setattr(app_database, 'update_profile_id_list', lambda: [profile])
    monkeypatch.setattr(indexer, 'database', fake_database)
    monkeypatch.setattr(indexer, 'settings', SimpleNamespace(general=SimpleNamespace(use_embedded_subs=True)))
    monkeypatch.setattr(indexer, 'get_subtitles', lambda *args, **kwargs: [dict(x) for x in subtitles])
    monkeypatch.setattr(indexer, 'get_language_equals', lambda: [])
    monkeypatch.setattr(indexer, 'event_stream', lambda **kwargs: None)

    run()

    return sorted(fake_database.missing)


# One profile item, no cutoff. Expected values are the missing list the profile should produce.
SINGLE_ITEM_CASES = [
    ('normal', 'none', ['en']),
    ('normal', 'normal', []),
    ('normal', 'hi', []),
    ('normal', 'forced', ['en']),
    ('normal', 'forced_hi', ['en']),
    ('hi', 'none', ['en:hi']),
    ('hi', 'normal', ['en:hi']),
    ('hi', 'hi', []),
    ('hi', 'forced', ['en:hi']),
    ('hi', 'forced_hi', ['en:hi']),
    ('non_hi', 'none', ['en']),
    ('non_hi', 'normal', []),
    ('non_hi', 'hi', ['en']),
    ('non_hi', 'forced', ['en']),
    ('non_hi', 'forced_hi', ['en']),
    ('forced', 'none', ['en:forced']),
    ('forced', 'normal', ['en:forced']),
    ('forced', 'hi', ['en:forced']),
    ('forced', 'forced', []),
    ('forced', 'forced_hi', ['en:forced']),
]
SINGLE_ITEM_IDS = [f'{item_type}-{actual}' for item_type, actual, _ in SINGLE_ITEM_CASES]


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('item_type, actual, expected', SINGLE_ITEM_CASES, ids=SINGLE_ITEM_IDS)
def test_single_item_profile_without_cutoff(monkeypatch, indexer, item_type, actual, expected):
    profile = _profile([_profile_item(1, item_type)])

    assert _missing(monkeypatch, indexer, profile, ACTUAL[actual]) == sorted(expected)


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('cutoff', ['item', 'any'])
@pytest.mark.parametrize('item_type, actual, expected', SINGLE_ITEM_CASES, ids=SINGLE_ITEM_IDS)
def test_single_item_profile_with_cutoff(monkeypatch, indexer, cutoff, item_type, actual, expected):
    # A cutoff on the only profile item is met exactly when that item is satisfied, so the result
    # must equal the no-cutoff result.
    profile = _profile([_profile_item(1, item_type)], cutoff=1 if cutoff == 'item' else ANY_CUTOFF)

    assert _missing(monkeypatch, indexer, profile, ACTUAL[actual]) == sorted(expected)


MIXED_PROFILE = [
    _profile_item(1, 'normal'),
    _profile_item(2, 'hi'),
    _profile_item(3, 'normal', language='pl'),
]


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('cutoff, expected', [
    (None, ['en:hi', 'pl']),
    (1, []),
    (2, ['en:hi', 'pl']),
    (3, ['en:hi', 'pl']),
    (ANY_CUTOFF, []),
], ids=['no-cutoff', 'normal-item-cutoff-met', 'hi-item-cutoff-not-met',
        'other-language-cutoff-not-met', 'any-cutoff-met'])
def test_multi_item_profile_with_cutoff(monkeypatch, indexer, cutoff, expected):
    profile = _profile(MIXED_PROFILE, cutoff=cutoff)

    assert _missing(monkeypatch, indexer, profile, ACTUAL['normal']) == sorted(expected)


# A normal item and a non-HI item for the same language. While non-HI is requested, an HI subtitle does
# not satisfy the normal item, and the cutoff must agree with the missing list.
NON_HI_PAIR_PROFILE = [_profile_item(1, 'normal'), _profile_item(2, 'non_hi')]
NON_HI_PAIR_CUTOFF_CASES = [
    (None, 'hi', ['en', 'en']),
    (1, 'hi', ['en', 'en']),
    (2, 'hi', ['en', 'en']),
    (ANY_CUTOFF, 'hi', ['en', 'en']),
    (None, 'normal', []),
    (1, 'normal', []),
    (2, 'normal', []),
    (ANY_CUTOFF, 'normal', []),
]


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('cutoff, actual, expected', NON_HI_PAIR_CUTOFF_CASES,
                         ids=[f'{cutoff}-{actual}' for cutoff, actual, _ in NON_HI_PAIR_CUTOFF_CASES])
def test_normal_and_non_hi_pair_with_cutoff(monkeypatch, indexer, cutoff, actual, expected):
    profile = _profile(NON_HI_PAIR_PROFILE, cutoff=cutoff)

    assert _missing(monkeypatch, indexer, profile, ACTUAL[actual]) == sorted(expected)


# Two profile items for the same language. Each unordered pair is tested in both profile orders:
# the result must not depend on which item comes first.
PAIR_CASES = {
    ('normal', 'hi'): {'none': ['en', 'en:hi'], 'normal': ['en:hi'], 'hi': [], 'forced': ['en', 'en:hi'],
                       'forced_hi': ['en', 'en:hi']},
    ('non_hi', 'hi'): {'none': ['en', 'en:hi'], 'normal': ['en:hi'], 'hi': ['en'], 'forced': ['en', 'en:hi'],
                       'forced_hi': ['en', 'en:hi']},
    ('normal', 'non_hi'): {'none': ['en', 'en'], 'normal': [], 'hi': ['en', 'en'], 'forced': ['en', 'en'],
                           'forced_hi': ['en', 'en']},
    ('normal', 'forced'): {'none': ['en', 'en:forced'], 'normal': ['en:forced'], 'hi': ['en:forced'],
                           'forced': ['en'], 'forced_hi': ['en', 'en:forced']},
    ('non_hi', 'forced'): {'none': ['en', 'en:forced'], 'normal': ['en:forced'], 'hi': ['en', 'en:forced'],
                           'forced': ['en'], 'forced_hi': ['en', 'en:forced']},
    ('hi', 'forced'): {'none': ['en:hi', 'en:forced'], 'normal': ['en:hi', 'en:forced'], 'hi': ['en:forced'],
                       'forced': ['en:hi'], 'forced_hi': ['en:hi', 'en:forced']},
}
PAIR_PARAMS = [
    pytest.param(order, actual, expected, id=f'{order[0]}-{order[1]}-{actual}')
    for (first, second), outcomes in PAIR_CASES.items()
    for order in [(first, second), (second, first)]
    for actual, expected in outcomes.items()
]


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('order, actual, expected', PAIR_PARAMS)
def test_same_language_pair_is_independent_of_profile_order(monkeypatch, indexer, order, actual, expected):
    profile = _profile([_profile_item(1, order[0]), _profile_item(2, order[1])])

    assert _missing(monkeypatch, indexer, profile, ACTUAL[actual]) == sorted(expected)


@pytest.mark.parametrize('indexer', INDEXERS)
def test_issue_3647_reproduction(monkeypatch, indexer):
    # Profile from the issue. The English normal subtitle exists, so only en:hi and pl should be missing.
    # The issue text expects ['pl'], but the English HI item is also unmet by a normal subtitle, as in
    # the single-item ('hi', 'normal') case.
    profile = _profile([
        _profile_item(1, 'non_hi'),
        _profile_item(2, 'hi'),
        _profile_item(3, 'non_hi', language='pl'),
    ])

    assert _missing(monkeypatch, indexer, profile, ACTUAL['normal']) == sorted(['en:hi', 'pl'])
