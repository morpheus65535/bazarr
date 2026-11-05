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
    from app.database import TableSportsEvents, TableSportsLeagues, database, delete, insert

    # One event wants two languages, so the sports count reads its missing list.
    database.execute(insert(TableSportsLeagues).values(
        sportarrLeagueId=9001, title="UFC", path="/sports/UFC", monitored="True", tags="[]"))
    database.execute(insert(TableSportsEvents).values(
        sportarrLeagueId=9001, sportarrEventId=9001, title="UFC 318", path="/sports/UFC/UFC 318.mkv",
        season=2026, episode=1, monitored="True", missing_subtitles="['en', 'es']"))
    try:
        response = api_client.get("/api/badges", headers={"X-API-KEY": api_key})
    finally:
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
