from datetime import datetime
from importlib import import_module
from pathlib import Path
from types import ModuleType
from uuid import uuid4
import sys

from flask import Flask


def test_sports_leagues_list_filters_sorts_and_counts(monkeypatch):
    api_path = Path(__file__).resolve().parents[2] / 'bazarr' / 'api'
    api_package = ModuleType('api')
    api_package.__path__ = [str(api_path)]
    sports_package = ModuleType('api.sports')
    sports_package.__path__ = [str(api_path / 'sports')]
    monkeypatch.setitem(sys.modules, 'api', api_package)
    monkeypatch.setitem(sys.modules, 'api.sports', sports_package)
    SportsLeagues = import_module('api.sports.leagues').SportsLeagues
    from app.config import settings
    from app.database import TableSportsEvents, TableSportsLeagues, database, delete, insert

    token = uuid4().hex[:8]
    ids = [int(token, 16) + offset for offset in range(3)]
    monkeypatch.setattr(settings.sportarr, 'excluded_tags', [])
    monkeypatch.setattr(settings.sportarr, 'excluded_sports', [])
    monkeypatch.setattr(settings.sportarr, 'only_monitored', False)

    try:
        for offset, title, monitored, profile, sport, language, tag in [
            (0, 'Alpha', 'True', None, 'Soccer', "['English']", 'A'),
            (1, 'Beta', 'False', None, 'Fighting', "['French']", 'B'),
            (2, 'Gamma', 'True', None, 'Soccer', "['English']", 'A'),
        ]:
            database.execute(insert(TableSportsLeagues).values(
                sportarrLeagueId=ids[offset], title=title, sortTitle=title,
                path=f'/tmp/bazarr-sports-list-{token}-{offset}', monitored=monitored,
                profileId=profile, sport=sport, audio_language=language,
                tags=str([tag]), created_at_timestamp=datetime(2026, 1, offset + 1)))

        for offset, missing in [(0, "['en']"), (1, '[]'), (2, '[]')]:
            database.execute(insert(TableSportsEvents).values(
                id=ids[0] * 10 + offset, sportarrEventId=ids[0] * 10 + offset,
                sportarrLeagueId=ids[0], season=2026, episode=offset + 1,
                title='Event', path=f'/tmp/bazarr-sports-list-{token}-event-{offset}',
                missing_subtitles=missing))
        database.execute(insert(TableSportsEvents).values(
            id=ids[1] * 10, sportarrEventId=ids[1] * 10,
            sportarrLeagueId=ids[1], season=2026, episode=1,
            title='Event', path=f'/tmp/bazarr-sports-list-{token}-event-b',
            missing_subtitles='[]'))

        app = Flask(__name__)

        def fetch(params):
            query = [("leagueid[]", league_id) for league_id in ids] + list(params.items())
            with app.test_request_context('/sports/leagues', query_string=query):
                return SportsLeagues.get.__wrapped__(SportsLeagues())

        all_leagues = fetch({'sort_by': 'episodeFileCount', 'sort_order': 'desc'})
        assert [row['sportarrLeagueId'] for row in all_leagues['data']] == ids
        assert all_leagues['total'] == 3
        assert [(row['episodeFileCount'], row['episodeMissingCount'])
                for row in all_leagues['data']] == [(3, 1), (1, 0), (0, 0)]
        assert all_leagues['data'][0]['created_at_timestamp'] is not None

        missing = fetch({'missing': 'true'})
        assert [row['sportarrLeagueId'] for row in missing['data']] == ids[:1]
        assert missing['total'] == 1

        filtered = fetch({'monitored': 'true', 'audio_language': 'English', 'tags[]': 'A',
                          'sort_by': 'createdAtTimestamp', 'sort_order': 'desc', 'length': 1})
        assert [row['sportarrLeagueId'] for row in filtered['data']] == ids[2:]
        assert filtered['total'] == 2

        no_profile = fetch({'profileid': 'none', 'missing': 'false'})
        assert [row['sportarrLeagueId'] for row in no_profile['data']] == ids[1:]
    finally:
        database.execute(delete(TableSportsEvents).where(TableSportsEvents.sportarrLeagueId.in_(ids)))
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId.in_(ids)))
        database.commit()
