"""
Missing subtitles for enhanced profiles, run through the real series and movies indexers.

Expectations follow the enhanced rules: a group is satisfied by all its items (AND) or any of them (OR), a satisfied
group adds nothing to the missing list, and the cutoff is a group id (65535 for any group, None for never).
"""
import pytest

from tests.bazarr.test_missing_subtitles_indexer import INDEXERS, _missing, _profile_item


def _sub(code, hi=False, forced=False):
    return {'path': f'/media/{code}.srt', 'code2': code, 'forced': forced, 'hi': hi}


def _group(group_id, operator, *items):
    return {'id': group_id, 'operator': operator, 'items': list(items)}


def _enhanced(groups, cutoff=None):
    # Same shape update_profile_id_list() returns for an enhanced profile: flat items plus groups.
    flat_items = [item for group in groups for item in group['items']]
    return {'profileId': 1, 'name': 'enhanced', 'cutoff': cutoff, 'profileType': 'enhanced',
            'items': flat_items, 'groups': groups,
            'mustContain': [], 'mustNotContain': [], 'originalFormat': False, 'tag': None}


EN = _sub('en')
FR = _sub('fr')
DE = _sub('de')
EN_HI = _sub('en', hi=True)

# Group 1 (AND): en and fr. Group 2 (OR): de or it.
G1 = _group(1, 'AND', _profile_item(1, 'normal', 'en'), _profile_item(2, 'normal', 'fr'))
G2 = _group(2, 'OR', _profile_item(3, 'normal', 'de'), _profile_item(4, 'normal', 'it'))
G3 = _group(3, 'AND', _profile_item(5, 'hi', 'en'))
G5 = _group(5, 'AND', _profile_item(7, 'non_hi', 'en'))
G6 = _group(6, 'AND', _profile_item(8, 'normal', 'en'))

CASES = [
    pytest.param([G1, G2], None, [], ['de', 'en', 'fr', 'it'], id='nothing-stored'),
    pytest.param([G1, G2], None, [EN], ['de', 'fr', 'it'], id='and-group-partly-satisfied'),
    pytest.param([G1, G2], 1, [EN, FR], [], id='and-cutoff-group-met'),
    pytest.param([G1, G2], 1, [EN], ['de', 'fr', 'it'], id='and-cutoff-group-not-met-searches-all-groups'),
    pytest.param([G1, G2], 1, [DE], ['en', 'fr'], id='higher-group-met-does-not-meet-cutoff'),
    pytest.param([G1, G2], 2, [DE], [], id='or-cutoff-group-met'),
    pytest.param([G1, G2], 65535, [DE], [], id='any-cutoff-met-by-or-group'),
    pytest.param([G1, G2], None, [DE], ['en', 'fr'], id='no-cutoff-never-met'),
    pytest.param([G1, G2], 65535, [EN], ['de', 'fr', 'it'], id='any-cutoff-no-group-met'),
    pytest.param([G1, G2], 9, [DE], ['en', 'fr'], id='cutoff-without-matching-group'),
    pytest.param([G6], None, [EN_HI], [], id='normal-item-satisfied-by-hi'),
    pytest.param([G3], None, [EN], ['en:hi'], id='hi-item-not-satisfied-by-normal'),
    pytest.param([G5], None, [EN_HI], ['en'], id='non-hi-item-not-satisfied-by-hi'),
    pytest.param([_group(2, 'AND', _profile_item(3, 'normal', 'de')), G1], 2, [DE], [], id='and-single-item-cutoff'),
    pytest.param([G2, G1], 1, [EN, FR], [], id='reordered-groups-keep-cutoff-id'),
    pytest.param([G2, G1], 2, [DE], [], id='reordered-groups-or-cutoff'),
]


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('groups, cutoff, subtitles, expected', CASES)
def test_enhanced_profile_missing_subtitles(monkeypatch, indexer, groups, cutoff, subtitles, expected):
    profile = _enhanced(groups, cutoff)

    assert _missing(monkeypatch, indexer, profile, subtitles) == sorted(expected)


@pytest.mark.parametrize('indexer', INDEXERS)
@pytest.mark.parametrize('cutoff, expected', [(4, []), (None, ['en', 'fr'])],
                         ids=['group-removed-by-audio-is-satisfied', 'same-group-without-cutoff-is-reported'])
def test_group_with_all_items_removed_by_audio_options_is_satisfied(monkeypatch, indexer, cutoff, expected):
    audio_excluded = dict(_profile_item(6, 'normal', 'en'), audio_exclude='True')
    profile = _enhanced([_group(4, 'AND', audio_excluded), G1], cutoff)

    assert _missing(monkeypatch, indexer, profile, [], audio_language="['en']") == sorted(expected)
