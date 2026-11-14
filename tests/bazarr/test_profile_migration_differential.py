# coding=utf-8
"""
Differential tests for the basic to enhanced profile migration.

For every generated basic profile, subtitle set and audio state, the missing subtitles reported by the basic evaluator
must equal the missing subtitles reported by the enhanced evaluator for the converted profile.

Single-item profiles are covered exhaustively through the pure evaluator functions. Two and three item profiles are
covered by seeded all-pairs (pairwise) sets of editor-valid profiles, run through the pure functions and through the
real series and movies indexers. Profiles with two items that share language, hearing-impaired and forced values are
never generated, because the profile editor rejects them. One test pins the only known difference for them.
"""
import itertools
import random
from unittest import mock

import pytest
from subliminal_patch import core

import app.database as app_database
from app.profile_migration import convert_basic_profile
from subtitles.indexer import profile_requirements as requirements
from tests.bazarr.test_missing_subtitles_indexer import INDEXERS, _missing, _profile

LANGUAGES = ('en', 'ea', 'fr')
TYPE_FLAGS = {
    'normal': ('False', 'False'),
    'hi': ('False', 'True'),
    'non_hi': ('False', 'Excluded'),
    'forced': ('True', 'False'),
}
INCLUSIONS = {
    'always': ('False', 'False'),
    'audio_exclude': ('True', 'False'),
    'audio_only_include': ('False', 'True'),
}
AUDIO_CODES = {"[]": set(), "['en']": {'en'}, "['pl']": {'pl'}}
SUBTITLE_STATES = {
    'none': None,
    'normal': (False, False),
    'hi': (False, True),
    'forced': (True, False),
    'forced_hi': (True, True),
}
CUTOFF_CHOICES = [None, 65535, 1, 2, 3, 99]
SUBTITLE_SOURCES = ('external', 'embedded')
ITEM_OPTIONS = list(itertools.product(LANGUAGES, TYPE_FLAGS, INCLUSIONS))
LANG_EQUALS = core._LanguageEquals([])


def _item(item_id, option):
    language, type_name, inclusion = option
    forced, hi = TYPE_FLAGS[type_name]
    audio_exclude, audio_only_include = INCLUSIONS[inclusion]
    return {'id': item_id, 'language': language, 'forced': forced, 'hi': hi,
            'audio_exclude': audio_exclude, 'audio_only_include': audio_only_include}


def _subtitles(states, source):
    subtitles = []
    for language, state in zip(LANGUAGES, states):
        flags = SUBTITLE_STATES[state]
        if flags is None:
            continue
        forced, hi = flags
        path = None if source == 'embedded' else f'/media/{language}.{state}.srt'
        subtitles.append({'path': path, 'code2': language, 'forced': forced, 'hi': hi})
    return subtitles


def _evaluate_basic(items, cutoff, subtitles, audio):
    """Run the basic evaluator the way the indexers do, including the cutoff lookup."""
    profile = _profile(items, cutoff)
    with mock.patch.object(app_database, 'update_profile_id_list', return_value=[profile]):
        cutoff_items = app_database.get_profile_cutoff(profile_id=1)

    def matches_audio(language):
        return language['language'] in AUDIO_CODES[audio]

    return sorted(requirements.calculate_missing_subtitles(items, cutoff_items, subtitles, matches_audio, LANG_EQUALS))


def _evaluate_migrated(items, cutoff, subtitles, audio):
    """Run the enhanced evaluator on the converted profile, the way the indexers do."""
    items_object, new_cutoff = convert_basic_profile(items, cutoff)

    def matches_audio(language):
        return language['language'] in AUDIO_CODES[audio]

    return sorted(requirements.calculate_enhanced_missing_subtitles(
        items_object['groups'], new_cutoff, subtitles, matches_audio, LANG_EQUALS))


def _pairwise(domains, seed, is_valid, candidates=200, attempts=5000):
    """
    Return valid rows covering every value pair of every two factors that some valid row can produce.

    Rows are chosen greedily from a seeded generator, and only rows accepted by is_valid are used. A pair for which no
    valid row turns up within attempts random tries is left out, so the result covers every reachable pair.
    """
    rng = random.Random(seed)
    factor_pairs = list(itertools.combinations(range(len(domains)), 2))
    uncovered = {(i, a, j, b) for i, j in factor_pairs for a in domains[i] for b in domains[j]}
    rows = []
    while uncovered:
        i, a, j, b = rng.choice(sorted(uncovered, key=repr))
        best_row, best_cover, valid_found = None, -1, 0
        for _ in range(attempts):
            row = [rng.choice(domain) for domain in domains]
            row[i], row[j] = a, b
            if not is_valid(tuple(row)):
                continue
            valid_found += 1
            cover = sum(1 for x, y in factor_pairs if (x, row[x], y, row[y]) in uncovered)
            if cover > best_cover:
                best_row, best_cover = row, cover
            if valid_found >= candidates:
                break
        if best_row is None:
            uncovered.discard((i, a, j, b))
            continue
        rows.append(tuple(best_row))
        for x, y in factor_pairs:
            uncovered.discard((x, best_row[x], y, best_row[y]))
    return rows


def _decode(row, item_count):
    """Turn one pairwise row into (items, cutoff, subtitles, audio, source)."""
    items = [_item(k + 1, row[3 * k:3 * k + 3]) for k in range(item_count)]
    offset = 3 * item_count
    cutoff, states, audio, source = row[offset], row[offset + 1:offset + 4], row[offset + 4], row[offset + 5]
    return items, cutoff, _subtitles(states, source), audio, source


def _editor_allows(items):
    """Return False when two items share language, hearing-impaired and forced values (rejected by the editor)."""
    keys = [(item['language'], item['hi'], item['forced']) for item in items]
    return len(set(keys)) == len(keys)


def _pairwise_rows(item_count, seed):
    domains = []
    for _ in range(item_count):
        domains.extend([list(LANGUAGES), list(TYPE_FLAGS), list(INCLUSIONS)])
    domains.append(CUTOFF_CHOICES)
    domains.extend([list(SUBTITLE_STATES)] * len(LANGUAGES))
    domains.append(list(AUDIO_CODES))
    domains.append(list(SUBTITLE_SOURCES))

    def is_valid(row):
        return _editor_allows(_decode(row, item_count)[0])

    rows = []
    for row in _pairwise(domains, seed, is_valid):
        items, cutoff, subtitles, audio, source = _decode(row, item_count)
        rows.append((row, items, cutoff, subtitles, audio))
    return rows


def _mismatches(cases):
    failures = []
    for description, items, cutoff, subtitles, audio in cases:
        basic = _evaluate_basic(items, cutoff, subtitles, audio)
        migrated = _evaluate_migrated(items, cutoff, subtitles, audio)
        if basic != migrated:
            failures.append((description, basic, migrated))
    return failures


def test_single_item_profiles_match_after_migration_exhaustively():
    states_product = list(itertools.product(SUBTITLE_STATES, repeat=len(LANGUAGES)))
    cases = [((option, cutoff, states, audio), [_item(1, option)], cutoff, _subtitles(states, 'external'), audio)
             for option, cutoff, states, audio in itertools.product(
                 ITEM_OPTIONS, CUTOFF_CHOICES, states_product, AUDIO_CODES)]

    failures = _mismatches(cases)

    assert len(cases) == len(ITEM_OPTIONS) * len(CUTOFF_CHOICES) * len(states_product) * len(AUDIO_CODES)
    assert not failures, f'{len(failures)} mismatches, first: {failures[:3]}'


@pytest.mark.parametrize('item_count, seed', [(2, 1), (2, 2), (3, 3)],
                         ids=['two-items-a', 'two-items-b', 'three-items'])
def test_pairwise_profiles_match_after_migration(item_count, seed):
    cases = _pairwise_rows(item_count, seed)

    failures = _mismatches(cases)

    assert cases
    assert not failures, f'{len(failures)} mismatches, first: {failures[:3]}'


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('item_count, seed', [(2, 1), (3, 3)], ids=['two-items', 'three-items'])
def test_pairwise_profiles_match_through_indexers(monkeypatch, indexer, item_count, seed):
    failures = []
    for row, items, cutoff, subtitles, audio in _pairwise_rows(item_count, seed):
        profile = _profile(items, cutoff)
        basic = _missing(monkeypatch, indexer, profile, subtitles, audio_language=audio)

        items_object, new_cutoff = convert_basic_profile(items, cutoff)
        enhanced_profile = {'profileId': 1, 'name': 'converted', 'cutoff': new_cutoff, 'profileType': 'enhanced',
                            'items': [item for group in items_object['groups'] for item in group['items']],
                            'groups': items_object['groups'], 'mustContain': [], 'mustNotContain': [],
                            'originalFormat': False, 'tag': None}
        migrated = _missing(monkeypatch, indexer, enhanced_profile, subtitles, audio_language=audio)

        if basic != migrated:
            failures.append((row, basic, migrated))

    assert not failures, f'{len(failures)} mismatches, first: {failures[:3]}'


def test_identical_items_keep_duplicate_entries_only_in_basic_output():
    # Not reachable through the editor, which rejects repeated language, HI and forced values. The basic evaluator
    # lists the entry once per item, the enhanced evaluator once in total. The set of missing entries is the same.
    items = [_item(1, ('ea', 'forced', 'always')), _item(2, ('ea', 'forced', 'always'))]

    basic = _evaluate_basic(items, 99, [], '[]')
    migrated = _evaluate_migrated(items, 99, [], '[]')

    assert basic == ['ea:forced', 'ea:forced']
    assert migrated == ['ea:forced']
    assert sorted(set(basic)) == sorted(set(migrated))
