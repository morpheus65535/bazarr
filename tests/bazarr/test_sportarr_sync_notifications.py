from types import SimpleNamespace


def test_league_removal_notifies_the_sports_view(monkeypatch):
    from sportarr.sync import leagues

    events = []
    monkeypatch.setattr(leagues, 'event_stream', lambda **data: events.append(data))
    monkeypatch.setattr(leagues.database, 'execute', lambda statement: SimpleNamespace(first=lambda: (object(),)))

    leagues.update_one_league(24, action='deleted')

    assert events == [{'type': 'sports-league', 'action': 'delete', 'payload': 24}]


def test_event_removal_notifies_the_sports_view(monkeypatch):
    from sportarr.sync import events as sports_events

    sent = []
    event = SimpleNamespace(sportarrEventId=42, partNumber=0, to_dict=lambda: {})
    calls = []

    def execute(statement):
        calls.append(statement)
        if len(calls) == 1:
            return SimpleNamespace(all=lambda: [(event,)])
        return SimpleNamespace(first=lambda: None)

    monkeypatch.setattr(sports_events.database, 'execute', execute)
    monkeypatch.setattr(sports_events, 'get_events_from_sportarr_api', lambda **kwargs: [])
    monkeypatch.setattr(sports_events, 'event_stream', lambda **data: sent.append(data))
    monkeypatch.setattr(sports_events.settings.sportarr, 'sync_only_monitored_leagues', False)

    sports_events.sync_events(7)

    assert sent == [{'type': 'sports-event', 'action': 'delete', 'payload': 42}]
