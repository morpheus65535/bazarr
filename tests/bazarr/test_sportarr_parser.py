import pytest

from sportarr.sync.parser import eventParser


def test_event_parser_uses_sportarr_numbers_when_available():
    event = {
        'leagueId': 1, 'id': 2, 'title': 'Race', 'seasonNumber': 2026,
        'episodeNumber': 14, 'season': '2026', 'eventDate': '2026-09-29T00:00:00Z',
        'monitored': True,
    }
    file = {'filePath': '/sports/race.mkv', 'id': 3}

    parsed = eventParser(event, file)

    assert (parsed['season'], parsed['episode']) == (2026, 14)


def test_event_parser_keeps_unnumbered_manual_events_syncable():
    event = {
        'leagueId': 1, 'id': 2, 'title': 'Race', 'seasonNumber': None,
        'episodeNumber': None, 'season': '2026', 'eventDate': '2026-09-29T00:00:00Z',
        'monitored': True,
    }
    file = {'filePath': '/sports/race.mkv', 'id': 3}

    parsed = eventParser(event, file)

    assert (parsed['season'], parsed['episode']) == (2026, 0)


def test_event_parser_uses_event_year_without_season():
    event = {
        'leagueId': 1, 'id': 2, 'title': 'Race', 'seasonNumber': None,
        'episodeNumber': None, 'season': None, 'eventDate': '2025-12-31T23:00:00Z',
        'monitored': True,
    }
    file = {'filePath': '/sports/race.mkv', 'id': 3}

    parsed = eventParser(event, file)

    assert (parsed['season'], parsed['episode']) == (2025, 0)


@pytest.mark.parametrize('quality, expected', [
    ('WEBDL-1080p', ('WEBDL', '1080p')),
    ('Bluray-1080p Remux', ('Bluray', '1080p')),
    ('HDTV-720p', ('HDTV', '720p')),
    ('1080P WEBDL x264 AAC', ('WEBDL', '1080p')),
    ('2160P BLURAY HEVC TrueHD PROPER', ('BLURAY', '2160p')),
    ('4K WEBDL', ('WEBDL', '2160p')),
    ('720P', (None, '720p')),
    ('HDTV', ('HDTV', None)),
    ('Unknown', (None, None)),
    (None, (None, None)),
], ids=lambda value: str(value))
def test_event_parser_reads_both_quality_shapes(quality, expected):
    event = {'leagueId': 1, 'id': 2, 'title': 'Race', 'seasonNumber': 2026, 'episodeNumber': 1, 'monitored': True}
    file = {'filePath': '/sports/race.mkv', 'id': 3, 'quality': quality}

    parsed = eventParser(event, file)

    assert (parsed['format'], parsed['resolution']) == expected
