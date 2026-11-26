from collections.abc import Iterator
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.orm import Session

import subtitles.upgrade as upgrade
from subliminal_patch.score import MAX_SCORES


class _Section(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e


LEAGUE_ID = 5
EVENT_ROW_ID = 11
VIDEO_PATH = "/sports/UFC/Season 2026/UFC 300 - Main Card.mkv"
SUBTITLES_PATH = "/sports/UFC/Season 2026/UFC 300 - Main Card.en.srt"


@pytest.fixture
def sports_upgrade(memory_session: Session, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """The sports upgrade job on an in-memory database, with every side effect recorded."""
    from app.database import TableLanguagesProfiles, TableSportsEvents, TableSportsEventsSubtitles, TableSportsLeagues

    memory_session.add(TableLanguagesProfiles(profileId=1, name="English", items="[]"))
    memory_session.commit()
    memory_session.add(TableSportsLeagues(sportarrLeagueId=LEAGUE_ID, title="UFC", path="/sports/UFC", profileId=1))
    memory_session.commit()
    memory_session.add(TableSportsEvents(
        id=EVENT_ROW_ID, sportarrEventId=300, sportarrLeagueId=LEAGUE_ID, season=2026, episode=1, partNumber=3,
        partName="Main Card", title="UFC 300", path=VIDEO_PATH, sceneName="UFC.300.Main.Card.1080p.WEB-DL",
        audio_language="[]"))
    memory_session.commit()
    memory_session.add(TableSportsEventsSubtitles(
        language="en", hi=False, forced=False, path=SUBTITLES_PATH, sportsEventId=EVENT_ROW_ID,
        sportarrLeagueId=LEAGUE_ID))
    memory_session.commit()

    general = _Section(upgrade_subs=True, days_to_upgrade_subs=7, upgrade_manual=True, minimum_score_sports=90,
                       use_sonarr=False, use_radarr=False, use_sportarr=True)
    recorded = SimpleNamespace(generate=[], stored=[], history=[], notifications=[], session=memory_session,
                               general=general)

    def generate(*args: Any, **kwargs: Any) -> list[SimpleNamespace]:
        recorded.generate.append((args, kwargs))
        return [SimpleNamespace(message="Upgraded")]

    monkeypatch.setattr(upgrade, "database", memory_session)
    monkeypatch.setattr(upgrade, "settings", SimpleNamespace(general=general))
    monkeypatch.setattr(upgrade, "get_exclusion_clause", lambda media_type: [])
    monkeypatch.setattr(upgrade, "get_profiles_list",
                        lambda *args, **kwargs: {"items": [{"language": "en", "forced": "False", "hi": "False"}]})
    monkeypatch.setattr(upgrade, "get_providers", lambda: ["provider"])
    monkeypatch.setattr(upgrade, "get_audio_profile_languages", lambda audio_language: [])
    monkeypatch.setattr(upgrade, "generate_subtitles", generate)
    monkeypatch.setattr(upgrade, "store_subtitles_sports", lambda row_id: recorded.stored.append(row_id))
    monkeypatch.setattr(upgrade, "history_log_sports",
                        lambda *args, **kwargs: recorded.history.append((args, kwargs)))
    monkeypatch.setattr(upgrade, "send_notifications_sports", lambda *args: recorded.notifications.append(args))
    monkeypatch.setattr(upgrade.path_mappings, "path_replace_sports", lambda path: path)
    job = SimpleNamespace(cancel_event=SimpleNamespace(is_set=lambda: False))
    monkeypatch.setattr(upgrade.jobs_queue, "get_job", lambda job_id: job)
    monkeypatch.setattr(upgrade.jobs_queue, "update_job_progress", lambda *args, **kwargs: None)
    monkeypatch.setattr(upgrade.jobs_queue, "update_job_name", lambda *args, **kwargs: None)
    return recorded


def _add_history(session: Session, **values: Any) -> int:
    from app.database import TableHistorySports

    row = dict(action=1, description="Downloaded", language="en", provider="provider", score=300,
               score_out_of=MAX_SCORES["episode"], sportsEventId=EVENT_ROW_ID, sportarrLeagueId=LEAGUE_ID,
               subs_id="sub-1", subtitles_path=SUBTITLES_PATH, video_path=VIDEO_PATH, timestamp=datetime.now())
    row.update(values)
    history = TableHistorySports(**row)
    session.add(history)
    session.commit()
    return history.id


def test_sports_upgrade_searches_again_with_the_sports_settings(sports_upgrade: SimpleNamespace) -> None:
    history_id = _add_history(sports_upgrade.session, score=300)

    upgrade.upgrade_sports_subtitles(job_id=1)

    assert len(sports_upgrade.generate) == 1
    args, kwargs = sports_upgrade.generate[0]
    assert args == (VIDEO_PATH, [("en", "False", "False")], None, "UFC.300.Main.Card.1080p.WEB-DL", "UFC", "sports", 1)
    assert kwargs["is_upgrade"] is True
    assert kwargs["previous_subtitles_to_delete"] == SUBTITLES_PATH
    assert kwargs["forced_minimum_score"] == max(300, round(90 * MAX_SCORES["episode"] / 100))
    assert sports_upgrade.stored == [EVENT_ROW_ID]
    assert sports_upgrade.history[0][0][:3] == (3, LEAGUE_ID, EVENT_ROW_ID)
    assert sports_upgrade.history[0][1] == {"upgraded_from_id": history_id}
    assert sports_upgrade.notifications == [(LEAGUE_ID, EVENT_ROW_ID, "Upgraded")]


def test_sports_upgrade_keeps_the_first_download_as_the_origin(sports_upgrade: SimpleNamespace) -> None:
    first_id = _add_history(sports_upgrade.session, timestamp=datetime.now() - timedelta(days=2))
    upgraded_id = _add_history(sports_upgrade.session, action=3, score=310, upgradedFromId=first_id)

    assert upgrade.get_upgradable_sports_subtitles() == {upgraded_id: first_id}

    upgrade.upgrade_sports_subtitles(job_id=1)

    assert sports_upgrade.history[0][1] == {"upgraded_from_id": first_id}


@pytest.mark.parametrize("values", [
    pytest.param({"score": MAX_SCORES["episode"] - 2}, id="near the maximum score"),
    pytest.param({"timestamp": datetime.now() - timedelta(days=8)}, id="outside the upgrade window"),
    pytest.param({"subtitles_path": "/sports/UFC/gone.en.srt"}, id="subtitles no longer on disk"),
    pytest.param({"video_path": "/sports/UFC/replaced.mkv"}, id="video replaced"),
    pytest.param({"language": "fr"}, id="language no longer wanted"),
])
def test_sports_upgrade_skips_subtitles_that_cannot_be_upgraded(sports_upgrade: SimpleNamespace,
                                                                values: dict[str, Any]) -> None:
    _add_history(sports_upgrade.session, **values)

    upgrade.upgrade_sports_subtitles(job_id=1)

    assert sports_upgrade.generate == []


def test_sports_upgrade_searches_once_when_a_file_has_two_index_rows(sports_upgrade: SimpleNamespace) -> None:
    from app.database import TableSportsEventsSubtitles, TableSportsLeagues

    # An earlier branch build could index the same file under two leagues.
    sports_upgrade.session.add(TableSportsLeagues(sportarrLeagueId=6, title="UFC Archive", path="/sports/Archive"))
    sports_upgrade.session.commit()
    sports_upgrade.session.add(TableSportsEventsSubtitles(
        language="en", hi=False, forced=False, path=SUBTITLES_PATH, sportsEventId=EVENT_ROW_ID, sportarrLeagueId=6))
    sports_upgrade.session.commit()
    _add_history(sports_upgrade.session)

    upgrade.upgrade_sports_subtitles(job_id=1)

    assert len(sports_upgrade.generate) == 1


def test_sports_upgrade_logs_under_the_league_the_event_is_in_now(sports_upgrade: SimpleNamespace) -> None:
    from app.database import TableSportsLeagues

    # An earlier build left the history row under the league the event moved away from.
    sports_upgrade.session.add(TableSportsLeagues(sportarrLeagueId=6, title="Old League", path="/sports/Old"))
    sports_upgrade.session.commit()
    _add_history(sports_upgrade.session, sportarrLeagueId=6)

    upgrade.upgrade_sports_subtitles(job_id=1)

    assert sports_upgrade.history[0][0][1] == LEAGUE_ID
    assert sports_upgrade.generate[0][0][4] == "UFC"


def test_upgradable_sports_subtitles_follow_the_league_the_event_is_in_now(sports_upgrade: SimpleNamespace,
                                                                          monkeypatch: pytest.MonkeyPatch) -> None:
    from app.database import TableSportsLeagues

    sports_upgrade.session.add(TableSportsLeagues(sportarrLeagueId=6, title="Old League", path="/sports/Old"))
    sports_upgrade.session.commit()
    history_id = _add_history(sports_upgrade.session, sportarrLeagueId=6)
    # The exclusion clause names leagues, so the join decides which league it reads.
    monkeypatch.setattr(upgrade, "get_exclusion_clause", lambda media_type: [TableSportsLeagues.sportarrLeagueId != 6])

    assert upgrade.get_upgradable_sports_subtitles() == {history_id: None}


def test_sports_upgrade_follows_the_upgrade_setting(sports_upgrade: SimpleNamespace) -> None:
    _add_history(sports_upgrade.session)
    sports_upgrade.general["upgrade_subs"] = False

    upgrade.upgrade_sports_subtitles(job_id=1)

    assert sports_upgrade.generate == []


def test_upgrade_subtitles_runs_the_sports_job_when_sportarr_is_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    general = _Section(use_sonarr=False, use_radarr=False, use_sportarr=True)
    monkeypatch.setattr(upgrade, "settings", SimpleNamespace(general=general))
    monkeypatch.setattr(upgrade, "upgrade_sports_subtitles", lambda **kwargs: calls.append(kwargs))

    upgrade.upgrade_subtitles(wait_for_completion=True)
    general["use_sportarr"] = False
    upgrade.upgrade_subtitles(wait_for_completion=True)

    assert calls == [{"wait_for_completion": True}]


@pytest.fixture
def sports_history_rows(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, int]]:
    """One event with an English and a French subtitles file, and history for both plus a removed German file."""
    from app.database import (TableHistorySports, TableLanguagesProfiles, TableSportsEvents,
                              TableSportsEventsSubtitles, TableSportsLeagues, database, delete, insert)
    import api.sports.history as sports_history

    monkeypatch.setattr(sports_history, "_language_still_desired", lambda language, profile_id: True)
    league_id, event_id, profile_id = 9201, 9201, 9201
    database.execute(insert(TableLanguagesProfiles).values(profileId=profile_id, name="Sports upgrade", items="[]"))
    database.execute(insert(TableSportsLeagues).values(
        sportarrLeagueId=league_id, title="UFC", sortTitle="UFC", path="/sports/9201", monitored="True", tags="[]",
        profileId=profile_id))
    database.execute(insert(TableSportsEvents).values(
        id=event_id, sportarrLeagueId=league_id, sportarrEventId=event_id, partNumber=0, title="UFC 300",
        path="/sports/9201/ufc300.mkv", season=2026, episode=1, monitored="True"))
    database.execute(insert(TableSportsEventsSubtitles), [
        {"language": language, "hi": False, "forced": False, "path": f"/sports/9201/ufc300.{language}.srt",
         "sportsEventId": event_id, "sportarrLeagueId": league_id} for language in ("en", "fr")
    ])
    ids = {}
    for language in ("en", "fr", "de"):
        ids[language] = database.execute(insert(TableHistorySports).values(
            action=1, description="Downloaded", language=language, provider="provider", score=200,
            score_out_of=MAX_SCORES["episode"], sportsEventId=event_id, sportarrLeagueId=league_id,
            subs_id=f"sub-{language}", subtitles_path=f"/sports/9201/ufc300.{language}.srt",
            video_path="/sports/9201/ufc300.mkv", timestamp=datetime.now())).inserted_primary_key[0]
    try:
        yield ids
    finally:
        database.execute(delete(TableHistorySports).where(TableHistorySports.sportsEventId == event_id))
        database.execute(delete(TableSportsEventsSubtitles).where(TableSportsEventsSubtitles.sportsEventId == event_id))
        database.execute(delete(TableSportsEvents).where(TableSportsEvents.id == event_id))
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId == league_id))
        database.execute(delete(TableLanguagesProfiles).where(TableLanguagesProfiles.profileId == profile_id))


def test_sports_history_marks_each_subtitles_file_that_can_be_upgraded(api_client: Any, api_key: str,
                                                                       sports_history_rows: dict[str, int]) -> None:
    response = api_client.get("/api/sports/history?eventid=9201", headers={"X-API-KEY": api_key})

    assert response.status_code == 200
    upgradable = {row["language"]["code2"]: row["upgradable"] for row in response.json["data"]}
    # The French file is the second file of the event, and it still counts.
    assert upgradable == {"en": True, "fr": True, "de": False}


def test_sports_history_names_the_league_the_event_is_in_now(api_client: Any, api_key: str,
                                                            sports_history_rows: dict[str, int]) -> None:
    from app.database import TableHistorySports, TableSportsLeagues, database, delete, insert, update

    database.execute(insert(TableSportsLeagues).values(
        sportarrLeagueId=9202, title="Old League", sortTitle="Old League", path="/sports/9202", monitored="True",
        tags="[]"))
    try:
        # An earlier build left this history row under the league the event moved away from.
        database.execute(update(TableHistorySports).where(TableHistorySports.id == sports_history_rows["en"])
                         .values(sportarrLeagueId=9202))

        response = api_client.get("/api/sports/history?eventid=9201", headers={"X-API-KEY": api_key})

        rows = {row["language"]["code2"]: row for row in response.json["data"]}
        assert (rows["en"]["sportarrLeagueId"], rows["en"]["leagueTitle"]) == (9201, "UFC")
    finally:
        database.execute(update(TableHistorySports).where(TableHistorySports.sportarrLeagueId == 9202)
                         .values(sportarrLeagueId=9201))
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId == 9202))
