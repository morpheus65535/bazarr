# coding=utf-8
"""
Golden snapshot for the basic to enhanced profile conversion.

The library below is synthetic. It covers the profile shapes found in real databases: single languages, forced, HI and
non-HI items, every kind of cutoff, several languages, audio options, legacy duplicate item ids, and an extra key on an
item. Each (indexer, profile, subtitle set, audio state) combination is run through the real series or movies indexer
loop, with the profile read back from the database rows. The missing lists produced before the conversion are stored in
tests/bazarr/golden/profile_conversion_missing.json. After the conversion the same combinations must reproduce them.

To regenerate the golden file after an intentional change to the basic evaluator, run the snapshot test with
UPDATE_PROFILE_GOLDEN=1 and review the diff.
"""
import copy
import json
import os
from pathlib import Path

import pytest
from sqlalchemy import insert

import app.database as app_database
from app.database import TableLanguagesProfiles, convert_basic_languages_profiles_to_enhanced, select
from subtitles.indexer import movies as movies_indexer
from subtitles.indexer import series as series_indexer
from tests.bazarr.test_missing_subtitles_indexer import _missing

GOLDEN_FILE = Path(__file__).parent / 'golden' / 'profile_conversion_missing.json'
INDEXERS = {'series': series_indexer, 'movies': movies_indexer}


def _item(item_id, language, hi='False', forced='False', audio_exclude='False', audio_only_include='False', **extra):
    return {'id': item_id, 'language': language, 'hi': hi, 'forced': forced, 'audio_exclude': audio_exclude,
            'audio_only_include': audio_only_include, **extra}


# profileId: (name, cutoff, items)
LIBRARY_PROFILES = {
    1: ('English', None, [_item(1, 'en')]),
    2: ('French', None, [_item(1, 'fr')]),
    3: ('English Forced', None, [_item(1, 'en', forced='True')]),
    4: ('English HI', None, [_item(1, 'en', hi='True')]),
    5: ('English Any', 65535, [_item(1, 'en'), _item(2, 'en', hi='True'), _item(3, 'en', forced='True')]),
    6: ('English non-HI', 1, [_item(1, 'en', hi='Excluded', non_hi_only='False')]),
    7: ('English then French, cutoff French', 2, [_item(1, 'en'), _item(2, 'fr')]),
    8: ('Four languages, cutoff third', 3, [_item(1, 'en'), _item(2, 'fr'), _item(3, 'el'), _item(4, 'ko')]),
    9: ('Audio exclude', None, [_item(1, 'en', audio_exclude='True'), _item(2, 'fr')]),
    10: ('Audio only cutoff', 1, [_item(1, 'en', audio_only_include='True'), _item(2, 'fr')]),
    11: ('Legacy duplicate ids with cutoff', 1, [_item(1, 'en'), _item(1, 'fr'), _item(2, 'de')]),
    12: ('HI and non-HI English', None, [_item(1, 'en', hi='True'), _item(2, 'en', hi='Excluded')]),
    13: ('Custom codes, cutoff second', 2, [_item(1, 'ea'), _item(2, 'pb')]),
}


def _sub(code, hi=False, forced=False):
    return {'path': f'/media/{code}.srt', 'code2': code, 'forced': forced, 'hi': hi}


SUBTITLE_SETS = {
    'none': [],
    'en': [_sub('en')],
    'en-hi': [_sub('en', hi=True)],
    'en-forced': [_sub('en', forced=True)],
    'en-forced-and-en': [_sub('en', forced=True), _sub('en')],
    'en-and-fr': [_sub('en'), _sub('fr')],
    'en-hi-and-fr': [_sub('en', hi=True), _sub('fr')],
    'fr': [_sub('fr')],
    'ea': [_sub('ea')],
    'de': [_sub('de')],
}
AUDIO_STATES = ['[]', "['en']", "['pl']"]


def insert_library(session):
    """Store the library profiles as basic rows, the way the settings endpoint did before the conversion."""
    for profile_id, (name, cutoff, items) in LIBRARY_PROFILES.items():
        session.execute(insert(TableLanguagesProfiles).values(
            profileId=profile_id, name=name, cutoff=cutoff, items=json.dumps(items), mustContain='[]',
            mustNotContain='[]', originalFormat=None, tag=f'tag-{profile_id}' if profile_id == 2 else None,
            profileType='basic'))
    session.commit()
    app_database.update_profile_id_list.invalidate()


def snapshot(monkeypatch):
    """Return the missing list for every (indexer, profile, subtitle set, audio state) combination."""
    # Read every profile before the indexer helper starts patching the profile list.
    profiles = {profile_id: app_database.get_profiles_list(profile_id=profile_id) for profile_id in LIBRARY_PROFILES}
    results = {}
    for profile_id, profile in profiles.items():
        # The indexer helper answers lookups for media rows that use profile 1, so the profile is presented as 1.
        for indexer_name, indexer in INDEXERS.items():
            for subtitles_name, subtitles in SUBTITLE_SETS.items():
                for audio in AUDIO_STATES:
                    key = f'{indexer_name}|{profile_id}|{subtitles_name}|{audio}'
                    results[key] = _missing(monkeypatch, indexer, dict(copy.deepcopy(profile), profileId=1),
                                            copy.deepcopy(subtitles), audio_language=audio)
    return results


@pytest.fixture
def library_db(memory_session, monkeypatch):
    monkeypatch.setattr(app_database, 'database', memory_session)
    insert_library(memory_session)
    return memory_session


def test_library_matches_golden_before_conversion(library_db, monkeypatch):
    results = snapshot(monkeypatch)

    if os.environ.get('UPDATE_PROFILE_GOLDEN'):
        GOLDEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN_FILE.write_text(json.dumps(results, indent=1, sort_keys=True) + '\n')
        pytest.skip('golden file regenerated')

    assert GOLDEN_FILE.exists(), 'run with UPDATE_PROFILE_GOLDEN=1 to create the golden file'
    golden = json.loads(GOLDEN_FILE.read_text())
    assert results == golden


def test_library_after_conversion_reproduces_golden(library_db, monkeypatch):
    convert_basic_languages_profiles_to_enhanced()
    app_database.update_profile_id_list.invalidate()
    converted = library_db.execute(select(TableLanguagesProfiles.profileType)).scalars().all()
    assert set(converted) == {'enhanced'}

    results = snapshot(monkeypatch)

    golden = json.loads(GOLDEN_FILE.read_text())
    mismatches = {key: (golden[key], results[key]) for key in golden if golden[key] != results[key]}
    assert set(results) == set(golden)
    assert not mismatches, f'{len(mismatches)} changed, first: {list(mismatches.items())[:3]}'
