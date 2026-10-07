from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from subliminal_patch.core import Language


@pytest.mark.parametrize(
    "profile_hi, actual_code, actual_hi, actual_forced, profile_code, equals, cutoff, extra_code, expected, profile_forced",
    [
        ("Excluded", "en", True, False, "en", [], False, None, "['en']", False),
        ("Excluded", "en", False, False, "en", [], False, None, "[]", False),
        ("Excluded", "en", False, True, "en", [], False, None, "['en']", False),
        ("False", "en", True, False, "en", [], False, None, "[]", False),
        ("False", "es", False, False, "en", [], False, None, "['en']", False),
        ("False", "es", False, False, "en", [(Language("spa"), Language("eng"))], False, None, "[]", False),
        ("Excluded", "es", False, False, "en", [(Language("spa"), Language("eng"))], False, None, "[]", False),
        ("Excluded", "en", False, False, "en", [], True, "es", "[]", False),
        ("Excluded", "en", True, False, "en", [], True, "es", "['en', 'es']", False),
        ("Excluded", "en", False, True, "en", [], True, "es", "['en', 'es']", False),
        ("Excluded", "es", False, False, "en", [(Language("spa"), Language("eng"))], True, "fr", "[]", False),
        ("Excluded", "en", False, True, "en", [], False, None, "[]", True),
        ("Excluded", "en", False, False, "en", [], False, None, "['en:forced']", True),
        ("False", "en", True, True, "en", [], False, None, "[]", True),
    ],
)
def test_sports_missing_subtitles_respects_hi_profile(
    monkeypatch, profile_hi, actual_code, actual_hi, actual_forced, profile_code,
    equals, cutoff, extra_code, expected, profile_forced
):
    from subtitles.indexer import sports

    event = SimpleNamespace(
        sportarrLeagueId=1,
        sportsEventId=2,
        profileId=3,
        audio_language="",
    )
    updates = []

    def execute(statement):
        if statement.is_select:
            return SimpleNamespace(all=lambda: [event])
        updates.append(statement.compile().params["missing_subtitles"])

    profile = {
        "items": [{
            "language": profile_code, "forced": str(profile_forced), "hi": profile_hi,
            "audio_exclude": "False", "audio_only_include": "False",
        }]
    }
    if extra_code:
        profile["items"].append({
            "language": extra_code, "forced": "False", "hi": "False",
            "audio_exclude": "False", "audio_only_include": "False",
        })
    monkeypatch.setattr(sports.database, "execute", execute)
    monkeypatch.setattr(sports, "get_profiles_list", lambda **kwargs: profile)
    monkeypatch.setattr(sports, "get_profile_cutoff", lambda **kwargs: profile["items"][:1] if cutoff else [])
    monkeypatch.setattr(sports, "get_language_equals", lambda: equals)
    monkeypatch.setattr(sports, "get_audio_profile_languages", lambda _: [])
    monkeypatch.setattr(sports, "get_sports_subtitles", lambda **kwargs: [{
        "code2": actual_code, "forced": actual_forced, "hi": actual_hi, "path": None,
    }])
    monkeypatch.setattr(sports, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(sports.settings.general, "use_embedded_subs", True)

    sports.list_missing_subtitles_sports(evno=2)

    assert updates == [expected]


def test_sports_rescan_removes_old_attributes_for_same_embedded_track(monkeypatch, tmp_path):
    from app.database import TableSportsEventsSubtitles
    from subtitles.indexer import sports

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE table_sports_leagues ("sportarrLeagueId" INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('CREATE TABLE table_sports_events (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO table_sports_leagues VALUES (1)')
        connection.exec_driver_sql('INSERT INTO table_sports_events VALUES (2)')
    TableSportsEventsSubtitles.__table__.create(engine)
    video = tmp_path / "race.mkv"
    video.touch()

    with engine.begin() as connection:
        connection.execute(TableSportsEventsSubtitles.__table__.insert().values(
            sportarrLeagueId=1, sportsEventId=2, language="en", forced=False,
            hi=True, embedded_track_id=5,
        ))

        def execute(statement):
            if statement.is_select:
                return SimpleNamespace(first=lambda: SimpleNamespace(
                    sportarrLeagueId=1, path=str(video), file_id=3, file_size=0,
                ))
            return connection.execute(statement)

        monkeypatch.setattr(sports.database, "execute", execute)
        monkeypatch.setattr(sports.path_mappings, "path_replace_sports", lambda path: path)
        monkeypatch.setattr(sports, "embedded_subs_reader", lambda *args, **kwargs: [
            (5, "eng", False, False, "srt"),
        ])
        monkeypatch.setattr(sports, "alpha2_from_alpha3", lambda _: "en")
        monkeypatch.setattr(sports, "get_language_set", lambda: set())
        monkeypatch.setattr(sports, "search_external_subtitles", lambda *args, **kwargs: {})
        monkeypatch.setattr(sports, "guess_external_subtitles", lambda *args, **kwargs: {})
        monkeypatch.setattr(sports, "get_sports_subtitles", lambda **kwargs: [])
        monkeypatch.setattr(sports, "get_subtitle_destination_folder", lambda: None)
        monkeypatch.setattr(sports, "list_missing_subtitles_sports", lambda **kwargs: None)
        monkeypatch.setattr(sports.settings.general, "use_embedded_subs", True)
        monkeypatch.setattr(sports.settings.general, "ignore_pgs_subs", False)
        monkeypatch.setattr(sports.settings.general, "ignore_vobsub_subs", False)
        monkeypatch.setattr(sports.settings.general, "ignore_ass_subs", False)

        sports.store_subtitles_sports(2)

        rows = connection.execute(select(TableSportsEventsSubtitles)).all()

    assert len(rows) == 1
    assert rows[0].hi is False
