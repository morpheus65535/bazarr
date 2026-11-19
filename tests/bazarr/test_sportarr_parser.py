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
