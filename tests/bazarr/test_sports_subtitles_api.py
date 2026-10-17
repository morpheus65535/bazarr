from importlib import import_module
from io import BytesIO
from pathlib import Path
from types import ModuleType, SimpleNamespace
from uuid import uuid4
import sys


def test_sports_subtitle_actions_check_league_and_indexed_path(monkeypatch):
    api_path = Path(__file__).resolve().parents[2] / 'bazarr' / 'api'
    api_package = ModuleType('api')
    api_package.__path__ = [str(api_path)]
    sports_package = ModuleType('api.sports')
    sports_package.__path__ = [str(api_path / 'sports')]
    monkeypatch.setitem(sys.modules, 'api', api_package)
    monkeypatch.setitem(sys.modules, 'api.sports', sports_package)
    module = import_module('api.sports.sports_subtitles')
    from app.database import (TableSportsEvents, TableSportsEventsSubtitles, TableSportsLeagues,
                              TableLanguagesProfiles, database, delete, insert, update)

    token = uuid4().hex[:8]
    league_id = int(token, 16)
    event_id = league_id * 10
    subtitle_path = f'/tmp/bazarr-sports-api-{token}.en.srt'
    calls = []
    monkeypatch.setattr(module, 'delete_subtitles', lambda **kwargs: calls.append(kwargs) or True)
    monkeypatch.setattr(module, 'sports_event_download_specific_subtitles',
                        lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(module.path_mappings, 'path_replace_sports', lambda path: path)
    monkeypatch.setattr(module.path_mappings, 'path_replace_reverse_sports', lambda path: path)

    try:
        database.execute(insert(TableSportsLeagues).values(
            sportarrLeagueId=league_id, title='League', path=f'/tmp/bazarr-sports-api-{token}'))
        database.execute(insert(TableSportsEvents).values(
            id=event_id, sportarrEventId=event_id, sportarrLeagueId=league_id,
            season=2026, episode=1, title='Event', path=f'/tmp/bazarr-sports-api-{token}.mkv'))
        database.execute(insert(TableSportsEventsSubtitles).values(
            sportsEventId=event_id, sportarrLeagueId=league_id,
            path=subtitle_path, language='en', forced=False, hi=False))

        def invoke(method, params):
            monkeypatch.setattr(module.SportsSubtitles, f'{method}_request_parser',
                                SimpleNamespace(parse_args=lambda: params))
            handler = getattr(module.SportsSubtitles, method)
            return handler.__wrapped__(module.SportsSubtitles())

        base = {'leagueid': league_id, 'eventid': event_id, 'language': 'en',
                'forced': 'false', 'hi': 'false', 'path': subtitle_path}
        assert invoke('patch', {**base, 'leagueid': league_id + 1})[1] == 404
        assert invoke('delete', {**base, 'leagueid': league_id + 1})[1] == 404
        assert invoke('delete', {**base, 'path': subtitle_path + '.srt'})[1] == 404
        assert invoke('patch', base)[1] == 400
        assert calls == []

        database.execute(insert(TableLanguagesProfiles).values(
            profileId=league_id, name='English', items='[]'))
        database.execute(update(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId == league_id)
                         .values(profileId=league_id))
        assert invoke('patch', base) == ('', 204)
        assert invoke('delete', base) == ('', 204)
        assert calls[1]['subtitles_path'] == subtitle_path
        assert calls[1]['sports_event_id'] == event_id
    finally:
        database.execute(delete(TableSportsEventsSubtitles)
                         .where(TableSportsEventsSubtitles.sportsEventId == event_id))
        database.execute(delete(TableSportsEvents).where(TableSportsEvents.id == event_id))
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId == league_id))
        database.execute(delete(TableLanguagesProfiles)
                         .where(TableLanguagesProfiles.profileId == league_id))
        database.commit()


def test_sports_upload_works_without_a_league_profile(monkeypatch):
    import subtitles.upload as upload

    metadata = SimpleNamespace(id=11, sportarrLeagueId=5, profileId=None)
    monkeypatch.setattr(upload.database, 'execute', lambda statement: SimpleNamespace(first=lambda: metadata))
    monkeypatch.setattr(upload, 'get_profiles_list', lambda profile_id: [])
    monkeypatch.setattr(upload, 'get_audio_profile_languages', lambda audio_language: [])
    monkeypatch.setattr(upload, 'get_target_folder', lambda path: '/subs')
    monkeypatch.setattr(upload, 'save_subtitles', lambda *args, **kwargs: [
        SimpleNamespace(storage_path='/subs/event.en.srt')])
    monkeypatch.setattr(upload, 'sync_subtitles', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload, 'notify_sportarr', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(upload, 'store_subtitles_sports', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload, 'history_log_sports', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload.path_mappings, 'path_replace_reverse_sports', lambda path: path)
    monkeypatch.setattr(upload.settings.general, 'single_language', False)
    monkeypatch.setattr(upload.settings.general, 'use_postprocessing', False)
    monkeypatch.setattr(upload.settings.general, 'chmod_enabled', False)
    monkeypatch.setattr(upload.settings.general, 'utf8_encode', False)
    monkeypatch.setattr(upload.settings.general, 'subzero_mods', [])

    result = upload.manual_upload_subtitle(
        path='/sports/event.mkv', language='en', forced=False, hi=False,
        media_type='sports', subtitle=BytesIO(b'1\n00:00:00,000 --> 00:00:01,000\nHi\n'),
        filename='event.en.srt', audio_language='[]', job_id='job',
        sportarrLeagueId=5, sportsEventId=11)

    assert result == ('', 204)
