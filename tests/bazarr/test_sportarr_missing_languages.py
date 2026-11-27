"""
Missing languages that the subtitle search reloads for a sports event before each language.

Sports events keep their missing languages in TableMissingSubtitles under the event row id, like episodes and movies.
"""
import pytest

from app.database import TableMissingSubtitles, TableSportsEvents, TableSportsLeagues
from subtitles import download
from subtitles.download import parse_language_object, reload_missing_languages_from_db


@pytest.fixture
def sports_event(memory_session, monkeypatch):
    monkeypatch.setattr(download, "database", memory_session)
    monkeypatch.setattr(download.path_mappings, "path_replace_reverse_sports", lambda path: path)
    memory_session.add(TableSportsLeagues(sportarrLeagueId=1, path="/sports/f1", title="Formula 1"))
    memory_session.commit()
    # Two parts of one event share the Sportarr event id. Only the row id tells them apart.
    memory_session.add(TableSportsEvents(id=1, sportarrLeagueId=1, sportarrEventId=10, partNumber=1, season=2026,
                                         episode=1, title="Race", path="/sports/f1/qualifying.mkv",
                                         missing_subtitles_calculated=True))
    memory_session.add(TableSportsEvents(id=2, sportarrLeagueId=1, sportarrEventId=10, partNumber=2, season=2026,
                                         episode=1, title="Race", path="/sports/f1/race.mkv",
                                         missing_subtitles_calculated=True))
    memory_session.add(TableMissingSubtitles(media_type="sports", media_id=1, language="it"))
    memory_session.commit()

    def add(languages):
        for language in languages:
            memory_session.add(TableMissingSubtitles(media_type="sports", media_id=2, language=language))
        # The same id under another media type must not leak into the sports result.
        memory_session.add(TableMissingSubtitles(media_type="series", media_id=2, language="pt"))
        memory_session.commit()
        return "/sports/f1/race.mkv"

    return add


def test_reload_returns_the_missing_languages_of_the_event_part(sports_event):
    path = sports_event(['en', 'fr:hi', 'de:forced'])

    languages = reload_missing_languages_from_db(path, 'sports')

    assert sorted(parse_language_object(language) for language in languages) == ['de:forced', 'en', 'fr:hi']


def test_reload_returns_nothing_when_the_event_misses_nothing(sports_event):
    path = sports_event([])

    assert reload_missing_languages_from_db(path, 'sports') == []


def test_reload_returns_nothing_for_an_unknown_path(sports_event):
    sports_event(['en'])

    assert reload_missing_languages_from_db("/sports/f1/other.mkv", 'sports') == []
