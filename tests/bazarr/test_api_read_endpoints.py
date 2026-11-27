# -*- coding: utf-8 -*-
"""
Smoke tests for the main read endpoints of the API blueprint.

These only send GET requests against the test database, so they check status codes and
response shape rather than the data itself.
"""
import pytest


@pytest.mark.parametrize("path", ["/api/series", "/api/movies"])
def test_media_list_returns_data_and_total(api_client, api_key, path):
    response = api_client.get(path, headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    body = response.json
    assert isinstance(body["data"], list)
    assert isinstance(body["total"], int)
    assert body["total"] >= len(body["data"])


def test_system_health_returns_issue_list(api_client, api_key):
    response = api_client.get("/api/system/health", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    issues = response.json["data"]
    assert isinstance(issues, list)
    for issue in issues:
        assert set(issue) == {"object", "issue"}


def test_badges_returns_counts(api_client, api_key):
    from app.database import (TableMissingSubtitles, TableSportsEvents, TableSportsLeagues, database, delete,
                              insert)

    # One event wants two languages, so the sports count reads its missing-language rows.
    database.execute(insert(TableSportsLeagues).values(
        sportarrLeagueId=9001, title="UFC", path="/sports/UFC", monitored="True", tags="[]"))
    database.execute(insert(TableSportsEvents).values(
        id=9001, sportarrLeagueId=9001, sportarrEventId=9001, title="UFC 318", path="/sports/UFC/UFC 318.mkv",
        season=2026, episode=1, monitored="True", missing_subtitles_calculated=True))
    database.execute(insert(TableMissingSubtitles), [
        {"media_type": "sports", "media_id": 9001, "language": language} for language in ("en", "es")
    ])
    try:
        response = api_client.get("/api/badges", headers={"X-API-KEY": api_key})
    finally:
        database.execute(delete(TableMissingSubtitles).where(TableMissingSubtitles.media_type == "sports")
                         .where(TableMissingSubtitles.media_id == 9001))
        database.execute(delete(TableSportsEvents).where(TableSportsEvents.sportarrLeagueId == 9001))
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId == 9001))

    assert response.status_code == 200
    for key in ("episodes", "movies", "sports", "providers", "status", "announcements"):
        assert isinstance(response.json[key], int)
    assert response.json["sports"] >= 2


def test_subtitles_requires_subtitles_path(api_client, api_key):
    response = api_client.get("/api/subtitles", headers={"X-API-KEY": api_key})

    assert response.status_code == 400


def test_subtitles_returns_envelope_for_path(api_client, api_key, tmp_path):
    subtitle = tmp_path / "show.en.srt"
    subtitle.write_text("1\n00:00:01,000 --> 00:00:02,000\nHi\n", encoding="utf-8")

    response = api_client.get("/api/subtitles", query_string={"subtitlesPath": str(subtitle)},
                              headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    assert "data" in response.json


@pytest.fixture
def sports_rows():
    from app.database import (TableMissingSubtitles, TableSportsEvents, TableSportsLeagues, database, delete,
                              insert)

    league_ids = [9101, 9102]
    event_ids = [9101, 9102]
    database.execute(insert(TableSportsLeagues), [
        {"sportarrLeagueId": league_id, "title": f"League {league_id}", "sortTitle": f"League {league_id}",
         "path": f"/sports/{league_id}", "monitored": "True", "tags": "[]"} for league_id in league_ids
    ])
    # Two parts of one card. Only the first part misses languages.
    database.execute(insert(TableSportsEvents), [
        {"id": event_id, "sportarrLeagueId": 9101, "sportarrEventId": 9101, "partNumber": part, "title": "UFC 318",
         "partName": f"Part {part}", "path": f"/sports/9101/part-{part}.mkv", "season": 2026, "episode": 1,
         "monitored": "True", "missing_subtitles_calculated": True}
        for part, event_id in enumerate(event_ids, start=1)
    ])
    database.execute(insert(TableMissingSubtitles), [
        {"media_type": "sports", "media_id": 9101, "language": language} for language in ("en", "fr:hi")
    ])
    try:
        yield
    finally:
        database.execute(delete(TableMissingSubtitles).where(TableMissingSubtitles.media_type == "sports")
                         .where(TableMissingSubtitles.media_id.in_(event_ids)))
        database.execute(delete(TableSportsEvents).where(TableSportsEvents.id.in_(event_ids)))
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId.in_(league_ids)))


SPORTS_MISSING = [
    {"name": "English", "code2": "en", "code3": "eng", "forced": False, "hi": False},
    {"name": "French", "code2": "fr", "code3": "fra", "forced": False, "hi": True},
]


def test_sports_wanted_lists_missing_languages_from_the_shared_table(api_client, api_key, sports_rows):
    response = api_client.get("/api/sports/wanted?eventid[]=9101&eventid[]=9102", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    assert response.json["total"] == 1
    assert response.json["data"] == [{
        "leagueTitle": "League 9101", "eventTitle": "UFC 318", "partName": "Part 1", "missing_subtitles": SPORTS_MISSING,
        "sportarrLeagueId": 9101, "sportsEventId": 9101, "sceneName": None, "tags": [], "sport": None,
    }]


def test_sports_events_list_missing_languages_per_part(api_client, api_key, sports_rows):
    response = api_client.get("/api/sports/events?leagueid[]=9101", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    events = {event["sportsEventId"]: event for event in response.json["data"]}
    assert events[9101]["missing_subtitles"] == SPORTS_MISSING
    assert events[9102]["missing_subtitles"] == []
    assert set(events[9101]) == {
        "audio_language", "episode", "missing_subtitles", "monitored", "path", "season", "sportsEventId",
        "sportarrLeagueId", "subtitles", "title", "partName", "partNumber", "sceneName", "broadcastDate",
    }


def test_sports_leagues_count_files_and_missing_parts(api_client, api_key, sports_rows):
    response = api_client.get("/api/sports/leagues?leagueid[]=9101&leagueid[]=9102",
                              headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    counts = {league["sportarrLeagueId"]: (league["episodeFileCount"], league["episodeMissingCount"])
              for league in response.json["data"]}
    # A league with no events still reports zero, not null.
    assert counts == {9101: (2, 1), 9102: (0, 0)}
