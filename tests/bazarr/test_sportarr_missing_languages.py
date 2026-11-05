"""
Missing languages that the subtitle search reloads for a sports event before each language.

Sports events keep the missing list on the event row, so the reload reads TableSportsEvents.missing_subtitles.
"""
import pytest

from app.database import TableSportsEvents, TableSportsLeagues
from subtitles import download
from subtitles.download import parse_language_object, reload_missing_languages_from_db


@pytest.fixture
def sports_event(memory_session, monkeypatch):
    monkeypatch.setattr(download, "database", memory_session)
    monkeypatch.setattr(download.path_mappings, "path_replace_reverse_sports", lambda path: path)
    memory_session.add(TableSportsLeagues(sportarrLeagueId=1, path="/sports/f1", title="Formula 1"))
    memory_session.commit()

    def add(missing_subtitles):
        memory_session.add(TableSportsEvents(id=1, sportarrLeagueId=1, sportarrEventId=10, season=2026, episode=1,
                                             title="Race", path="/sports/f1/race.mkv",
                                             missing_subtitles=missing_subtitles))
        memory_session.commit()
        return "/sports/f1/race.mkv"

    return add


def test_reload_returns_the_missing_languages_of_the_event(sports_event):
    path = sports_event("['en', 'fr:hi', 'de:forced']")

    languages = reload_missing_languages_from_db(path, 'sports')

    assert [parse_language_object(language) for language in languages] == ['en', 'fr:hi', 'de:forced']


@pytest.mark.parametrize("missing_subtitles", ["[]", None])
def test_reload_returns_nothing_when_the_event_misses_nothing(sports_event, missing_subtitles):
    path = sports_event(missing_subtitles)

    assert reload_missing_languages_from_db(path, 'sports') == []


def test_reload_returns_nothing_for_an_unknown_path(sports_event):
    sports_event("['en']")

    assert reload_missing_languages_from_db("/sports/f1/other.mkv", 'sports') == []
