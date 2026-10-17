from importlib import import_module
from pathlib import Path
from types import ModuleType, SimpleNamespace
from uuid import uuid4
import sys


def test_sports_blacklist_only_deletes_indexed_subtitle_for_its_league(monkeypatch):
    api_path = Path(__file__).resolve().parents[2] / 'bazarr' / 'api'
    api_package = ModuleType('api')
    api_package.__path__ = [str(api_path)]
    sports_package = ModuleType('api.sports')
    sports_package.__path__ = [str(api_path / 'sports')]
    monkeypatch.setitem(sys.modules, 'api', api_package)
    monkeypatch.setitem(sys.modules, 'api.sports', sports_package)
    module = import_module('api.sports.blacklist')
    from app.database import (TableSportsEvents, TableSportsEventsSubtitles, TableSportsLeagues,
                              database, delete, insert)

    token = uuid4().hex[:8]
    league_id = int(token, 16)
    event_id = league_id * 10
    subtitle_path = f'/tmp/bazarr-sports-blacklist-{token}.en.srt'
    calls = []
    monkeypatch.setattr(module, 'blacklist_log_sports', lambda **kwargs: calls.append(('log', kwargs)))
    monkeypatch.setattr(module, 'delete_subtitles', lambda **kwargs: calls.append(('delete', kwargs)) or True)
    monkeypatch.setattr(module, 'sports_event_download_subtitles', lambda **kwargs: None)
    monkeypatch.setattr(module, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(module.path_mappings, 'path_replace_sports', lambda path: path)
    monkeypatch.setattr(module.path_mappings, 'path_replace_reverse_sports', lambda path: path)

    try:
        database.execute(insert(TableSportsLeagues).values(
            sportarrLeagueId=league_id, title='League', path=f'/tmp/bazarr-sports-blacklist-{token}'))
        database.execute(insert(TableSportsEvents).values(
            id=event_id, sportarrEventId=event_id, sportarrLeagueId=league_id,
            season=2026, episode=1, title='Event', path=f'/tmp/bazarr-sports-blacklist-{token}.mkv'))
        database.execute(insert(TableSportsEventsSubtitles).values(
            sportsEventId=event_id, sportarrLeagueId=league_id,
            path=subtitle_path, language='en', forced=False, hi=False))

        def invoke(league, path):
            params = {'leagueid': league, 'eventid': event_id, 'provider': 'provider',
                      'subs_id': '123', 'language': 'en', 'subtitles_path': path}
            monkeypatch.setattr(module.SportsBlacklist, 'post_request_parser',
                                SimpleNamespace(parse_args=lambda: params))
            return module.SportsBlacklist.post.__wrapped__(module.SportsBlacklist())

        assert invoke(league_id + 1, subtitle_path)[1] == 404
        assert invoke(league_id, subtitle_path + '.other')[1] == 404
        assert calls == []

        assert invoke(league_id, subtitle_path) == ('', 200)
        assert [call[0] for call in calls] == ['log', 'delete']
        assert calls[1][1]['subtitles_path'] == subtitle_path
    finally:
        database.execute(delete(TableSportsEventsSubtitles)
                         .where(TableSportsEventsSubtitles.sportsEventId == event_id))
        database.execute(delete(TableSportsEvents).where(TableSportsEvents.id == event_id))
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId == league_id))
        database.commit()
