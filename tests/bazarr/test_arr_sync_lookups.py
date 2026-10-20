from collections.abc import Iterator

import msgspec
import pytest

from radarr.movie_snapshot import Movie
from radarr.sync import parser as movies
from radarr.sync.utils import MOVIE_DECODER
from sonarr.sync import parser as series
from tests.helpers.arr_fixtures import movie_payload, series_payload, series_record
from utilities.arr_sync_lookups import ArrSyncLookups
from utilities.arr_types import ArrTag
from utilities.json_types import JsonValue


def test_tag_order_and_duplicate_catalogue_entries_are_preserved() -> None:
    tags: list[ArrTag] = [{'id': 2, 'label': 'second'}, {'id': 1, 'label': 'first'},
                          {'id': 2, 'label': 'second again'}, {'id': 3, 'label': 'first'}]
    lookups = ArrSyncLookups(tags, [], [])
    assert lookups.tags([1, 2, 2, 999]) == ['second', 'first', 'second again']
    assert lookups.tags([1, 3]) == ['first', 'first']
    assert lookups.tags([]) == []


def test_profile_priority_uses_profile_order() -> None:
    profiles = [(7, 'Preferred', 'a'), (9, 'Other', 'b'), (10, 'Duplicate', 'a'), (11, 'No tag', None)]
    lookups = ArrSyncLookups([], profiles, [])
    assert lookups.matching_profile(['b', 'a']) == 7
    assert lookups.matching_profile(['b']) == 9
    assert lookups.matching_profile(['unknown']) is None
    assert ArrSyncLookups([], [(0, 'Zero', 'a')], []).matching_profile(['a']) == 0


def test_audio_profiles_preserve_duplicates_and_id_equality() -> None:
    profiles: list[list[JsonValue]] = [[1, 'English'], [1.0, 'French'], ['1', 'German'],
                                     [[1], 'Invalid'], [True, 'Spanish']]
    lookups = ArrSyncLookups([], [], profiles)
    assert lookups.audio_languages(1) == ['English', 'French', 'Spanish']
    assert lookups.audio_languages(2) == []
    assert lookups.audio_languages(msgspec.UNSET) == []
    lookups.audio_languages(1).append('Mutation')
    assert lookups.audio_languages(1) == ['English', 'French', 'Spanish']


def test_unavailable_audio_profiles_fail_only_when_needed() -> None:
    lookups = ArrSyncLookups([], [], None)
    assert lookups.tags([]) == []
    with pytest.raises(TypeError):
        lookups.audio_languages(1)


def test_catalogue_is_consumed_once() -> None:
    seen: list[int] = []

    def catalogue() -> Iterator[ArrTag]:
        for identifier in range(100):
            seen.append(identifier)
            yield {'id': identifier, 'label': str(identifier)}

    lookups = ArrSyncLookups(catalogue(), [(7, 'Language', '2')], [[1, 'English']])
    for _ in range(20):
        assert lookups.tags([2, 7]) == ['2', '7']
        assert lookups.matching_profile(['2']) == 7
        assert lookups.audio_languages(1) == ['English']
    assert seen == list(range(100))


@pytest.mark.parametrize('kind', ['movie', 'series'])
def test_parsers_use_shared_lookups_and_live_tag_settings(kind: str, monkeypatch: pytest.MonkeyPatch) -> None:
    lookups = ArrSyncLookups([{'id': 1, 'label': 'a'}, {'id': 2, 'label': 'b'}],
                            [(7, 'Preferred', 'a'), (9, 'Other', 'b')], [[1, 'English']])
    monkeypatch.setattr(movies.get_radarr_info, 'is_legacy', lambda: True)
    monkeypatch.setattr(series.get_sonarr_info, 'is_legacy', lambda: True)
    monkeypatch.setattr(movies.settings.general, 'parse_embedded_audio_track', False)
    monkeypatch.setattr(movies.settings.general, 'movie_tag_enabled', True)
    monkeypatch.setattr(movies.settings.general, 'serie_tag_enabled', True)
    monkeypatch.setattr(movies.settings.general, 'remove_profile_tags', [])
    if kind == 'movie':
        movie = MOVIE_DECODER.complete_from_value(movie_payload())
        assert isinstance(movie, Movie)
        movie.tags = [2, 1]
        movie.qualityProfileId = 1

        def parse() -> dict[str, str | int | None]:
            result = movies.movieParser(movie, 'insert', lookups, None)
            return {'tags': result['tags'], 'profileId': result.get('profileId'), 'audio': result['audio_language']}
    else:
        show = series_record(series_payload())
        show.tags = [2, 1]
        show.qualityProfileId = 1

        def parse() -> dict[str, str | int | None]:
            result = series.seriesParser(show, 'insert', lookups, None)
            return {'tags': result['tags'], 'profileId': result.get('profileId'), 'audio': result['audio_language']}

    assert parse() == {'tags': "['a', 'b']", 'profileId': 7, 'audio': "['English']"}
    monkeypatch.setattr(movies.settings.general, 'remove_profile_tags', ['b'])
    assert parse()['profileId'] is None
