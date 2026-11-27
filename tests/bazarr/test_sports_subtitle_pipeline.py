from io import BytesIO
from threading import Event
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from subliminal import Episode
from subzero.language import Language


def _sports_subtitles_engine():
    from app.database import TableSportsEventsSubtitles

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE table_sports_leagues ("sportarrLeagueId" INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('CREATE TABLE table_sports_events (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO table_sports_leagues VALUES (1)')
        connection.exec_driver_sql('INSERT INTO table_sports_events VALUES (2)')
    TableSportsEventsSubtitles.__table__.create(engine)
    return engine


def test_sports_indexer_skips_a_subtitle_without_a_language(monkeypatch, tmp_path):
    from app.database import TableSportsEventsSubtitles
    from subtitles.indexer import sports

    video = tmp_path / "UFC 300.mkv"
    video.touch()
    for name in ("UFC 300.srt", "UFC 300.en.srt", "UFC 300.pb.hi.srt"):
        (tmp_path / name).write_text("1\n00:00:01,000 --> 00:00:02,000\nHi\n")
    engine = _sports_subtitles_engine()

    with engine.begin() as connection:
        def execute(statement):
            if statement.is_select:
                return SimpleNamespace(first=lambda: SimpleNamespace(
                    sportarrLeagueId=1, path=str(video), file_id=3, file_size=0))
            return connection.execute(statement)

        found = {
            # The language of this file cannot be guessed.
            "UFC 300.srt": None,
            "UFC 300.en.srt": Language("eng"),
            "UFC 300.pb.hi.srt": Language("por", "BR"),
        }
        monkeypatch.setattr(sports.database, "execute", execute)
        monkeypatch.setattr(sports.path_mappings, "path_replace_sports", lambda path: path)
        monkeypatch.setattr(sports.path_mappings, "path_replace_reverse_sports", lambda path: path)
        monkeypatch.setattr(sports, "alpha2_from_alpha3", {"eng": "en", "por": "pt"}.get)
        monkeypatch.setattr(sports, "get_language_set", lambda: set())
        monkeypatch.setattr(sports, "search_external_subtitles", lambda *args, **kwargs: dict(found))
        monkeypatch.setattr(sports, "guess_external_subtitles", lambda folder, subtitles, **kwargs: subtitles)
        monkeypatch.setattr(sports, "get_sports_subtitles", lambda **kwargs: [])
        monkeypatch.setattr(sports, "get_subtitle_destination_folder", lambda: None)
        monkeypatch.setattr(sports, "list_missing_subtitles_sports", lambda **kwargs: None)
        monkeypatch.setattr(sports.settings.general, "use_embedded_subs", False)
        monkeypatch.setattr(sports.settings.general, "subfolder", "current")

        sports.store_subtitles_sports(2)

        rows = connection.execute(select(TableSportsEventsSubtitles.language, TableSportsEventsSubtitles.hi)
                                  .order_by(TableSportsEventsSubtitles.language)).all()

    # The custom language reports HI in upper case, as it does for episodes.
    assert [tuple(row) for row in rows] == [("en", False), ("pb", True)]


class _FakeJobs:
    def __init__(self):
        self.job = SimpleNamespace(cancel_event=Event())
        self.added = []

    def add_job_from_function(self, *args, **kwargs):
        self.added.append(kwargs)

    def get_job(self, job_id):
        return self.job

    def update_job_progress(self, **kwargs):
        pass

    def update_job_name(self, **kwargs):
        pass


def test_sports_full_scan_is_cancellable(monkeypatch):
    from subtitles.indexer import sports

    jobs = _FakeJobs()
    indexed = []
    monkeypatch.setattr(sports, "jobs_queue", jobs)
    monkeypatch.setattr(sports, "store_subtitles_sports", lambda event_id, use_cache: indexed.append(event_id))
    monkeypatch.setattr(sports.database, "execute", lambda statement: SimpleNamespace(all=lambda: [
        SimpleNamespace(path="/sports/a.mkv", title="League", eventTitle="Event", id=1)]))

    sports.sports_full_scan_subtitles()
    assert jobs.added[0]["is_cancellable"] is True

    jobs.job.cancel_event.set()
    with pytest.raises(sports.JobCanceled):
        sports.sports_full_scan_subtitles(job_id=1, use_cache=True)
    assert indexed == []


def test_sports_download_refreshes_media_servers_without_a_sportarr_scan(monkeypatch):
    import requests
    import sportarr.media_refresh
    from subtitles import processing

    refreshed = []
    metadata = SimpleNamespace(id=11, sportarrLeagueId=5, season=2024, episode=3)
    monkeypatch.setattr(processing.database, "execute", lambda statement: SimpleNamespace(first=lambda: metadata))
    monkeypatch.setattr(processing.path_mappings, "path_replace_reverse_sports", lambda path: path)
    monkeypatch.setattr(sportarr.media_refresh, "refresh_sports_media_servers", refreshed.append)
    monkeypatch.setattr(processing, "call_external_webhook", lambda **kwargs: None)
    monkeypatch.setattr(processing, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(processing.event_tracker, "track_subtitles", lambda **kwargs: None)
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: pytest.fail("Sportarr must not be called"))
    monkeypatch.setattr(processing.settings.general, "use_postprocessing", False)
    monkeypatch.setattr(processing.settings.subsync, "use_subsync", False)

    subtitle = SimpleNamespace(provider_name="provider", uploader=None, release_info=None, language=Language("eng"),
                               storage_path="/sports/event.en.srt", id="sub", score=300, matches={"series"})
    result = processing.process_subtitle(subtitle=subtitle, media_type="sports", audio_language="English",
                                         path="/sports/event.mkv", max_score=360)

    assert result.path == "/sports/event.mkv"
    assert refreshed == ["/sports/event.mkv"]


def test_sports_delete_refreshes_media_servers(monkeypatch, tmp_path):
    from subtitles.tools import delete

    subtitle = tmp_path / "event.en.srt"
    subtitle.write_text("1\n00:00:01,000 --> 00:00:02,000\nHi\n")
    refreshed = []
    monkeypatch.setattr(delete.path_mappings, "path_replace_sports", lambda path: path)
    monkeypatch.setattr(delete.path_mappings, "path_replace_reverse_sports", lambda path: path)
    monkeypatch.setattr(delete, "store_subtitles_sports", lambda event_id: None)
    monkeypatch.setattr(delete, "history_log_sports", lambda *args, **kwargs: None)
    monkeypatch.setattr(delete, "refresh_sports_media_servers", refreshed.append)
    monkeypatch.setattr(delete, "event_stream", lambda **kwargs: None)
    monkeypatch.setattr(delete, "call_external_webhook", lambda **kwargs: None)

    assert delete.delete_subtitles(media_type="sports", language="en", forced=False, hi=False,
                                   media_path=str(tmp_path / "event.mkv"), subtitles_path=str(subtitle),
                                   sportarr_league_id=5, sports_event_id=11)

    assert refreshed == [str(tmp_path / "event.mkv")]


def test_sportarr_scan_client_is_gone():
    # The Sportarr contract says not to scan a league after writing a subtitle.
    with pytest.raises(ImportError):
        import sportarr.notify  # noqa: F401


def test_sports_upload_queues_the_sync_and_notifies(monkeypatch):
    import subtitles.upload as upload

    sync_calls = []
    notifications = []
    refreshed = []
    metadata = SimpleNamespace(id=11, sportarrLeagueId=5, profileId=None)
    monkeypatch.setattr(upload.database, 'execute', lambda statement: SimpleNamespace(first=lambda: metadata))
    monkeypatch.setattr(upload, 'get_profiles_list', lambda profile_id: [])
    monkeypatch.setattr(upload, 'get_audio_profile_languages', lambda audio_language: [])
    monkeypatch.setattr(upload, 'get_target_folder', lambda path: '/subs')
    monkeypatch.setattr(upload, 'save_subtitles', lambda *args, **kwargs: [
        SimpleNamespace(storage_path='/subs/event.en.srt')])
    monkeypatch.setattr(upload, 'sync_subtitles', lambda **kwargs: sync_calls.append(kwargs))
    monkeypatch.setattr(upload, 'refresh_sports_media_servers', refreshed.append)
    monkeypatch.setattr(upload, 'send_notifications_sports', lambda *args: notifications.append(args))
    monkeypatch.setattr(upload, 'event_stream', lambda **kwargs: None)
    monkeypatch.setattr(upload, 'store_subtitles_sports', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload, 'history_log_sports', lambda *args, **kwargs: None)
    monkeypatch.setattr(upload.path_mappings, 'path_replace_reverse_sports', lambda path: path)
    monkeypatch.setattr(upload.settings.general, 'single_language', False)
    monkeypatch.setattr(upload.settings.general, 'use_postprocessing', False)
    monkeypatch.setattr(upload.settings.general, 'chmod_enabled', False)
    monkeypatch.setattr(upload.settings.general, 'utf8_encode', False)
    monkeypatch.setattr(upload.settings.general, 'subzero_mods', [])
    monkeypatch.setattr(upload.settings.general, 'dont_notify_manual_actions', False)

    upload.manual_upload_subtitle(
        path='/sports/event.mkv', language='en', forced=False, hi=False,
        media_type='sports', subtitle=BytesIO(b'1\n00:00:00,000 --> 00:00:01,000\nHi\n'),
        filename='event.en.srt', audio_language='[]', job_id='job',
        sportarrLeagueId=5, sportsEventId=11)

    # Without the upload job id, the sync gets its own job and counts against concurrent_syncs.
    assert 'job_id' not in sync_calls[0]
    sync_calls[0]['callback']()
    assert refreshed == ['/sports/event.mkv']
    assert notifications == [(5, 11, 'English Subtitles manually uploaded.')]


@pytest.mark.parametrize("media_type", ["sports", "episode"])
def test_sports_subtitle_is_blacklisted_with_the_sports_ids(monkeypatch, media_type):
    from app import get_providers

    logged = []
    monkeypatch.setattr(get_providers, "blacklist_log_sports", lambda *args: logged.append(args))
    monkeypatch.setattr(get_providers, "blacklist_log", lambda *args: pytest.fail("not a series subtitle"))
    monkeypatch.setattr(get_providers, "blacklist_log_movie", lambda *args: pytest.fail("not a movie subtitle"))

    # A provider names the media type of a sports subtitle "episode".
    get_providers.blacklist_subtitle("provider", "sub", media_type,
                                     {"radarrId": None, "sonarrSeriesId": None, "sonarrEpisodeId": None,
                                      "sportarrLeagueId": 5, "sportsEventId": 11},
                                     Language("eng"))

    assert logged == [(5, 11, "provider", "sub", "en")]


def test_sports_must_get_blacklisted_reaches_the_sports_blacklist(monkeypatch):
    from app import get_providers
    from subliminal_patch import core
    from subliminal_patch.exceptions import MustGetBlacklisted

    logged = []
    monkeypatch.setattr(get_providers, "blacklist_log_sports", lambda *args: logged.append(args))

    class Provider:
        def download_subtitle(self, subtitle):
            raise MustGetBlacklisted(subtitle.id, "episode")

    pool = core.SZProviderPool({"provider"}, {}, throttle_callback=get_providers.provider_throttle)
    pool.initialized_providers["provider"] = Provider()
    subtitle = SimpleNamespace(provider_name="provider", id="sub", language=Language("eng"),
                               sportarrLeagueId=5, sportsEventId=11)

    assert pool.download_subtitle(subtitle) is False
    assert logged == [(5, 11, "provider", "sub", "en")]


def test_undecodable_sports_subtitle_is_blacklisted(monkeypatch):
    from subtitles import download

    blacklisted = []
    monkeypatch.setattr(download, "blacklist_subtitle", lambda *args: blacklisted.append(args))
    video = SimpleNamespace(sportarrLeagueId=5, sportsEventId=11)
    subtitle = SimpleNamespace(id="sub", provider_name="provider")

    download._blacklist_unusable_subtitles(video, [subtitle], "sports", Language("eng"))

    ids = blacklisted[0][3]
    assert blacklisted[0][2] == "sports"
    assert (ids["sportarrLeagueId"], ids["sportsEventId"]) == (5, 11)


def test_sports_pools_use_the_sports_blacklist(monkeypatch):
    from subtitles import pool as pool_module

    updates = []
    existing = SimpleNamespace(update=lambda *args: updates.append(args))
    monkeypatch.setattr(pool_module, "get_providers", lambda: ["embeddedsubtitles"])
    monkeypatch.setattr(pool_module, "get_providers_auth", lambda: {})
    monkeypatch.setattr(pool_module, "get_blacklist_sports", lambda: [("provider", "sports")])
    monkeypatch.setattr(pool_module, "get_blacklist_movie", lambda: [("provider", "movie")])
    monkeypatch.setattr(pool_module, "get_ban_list", lambda profile_id: None)
    monkeypatch.setattr(pool_module, "get_language_equals", lambda: [])
    monkeypatch.setitem(pool_module._embedded_pools, "sports_1", existing)

    assert pool_module._get_embedded_pool("sports", 1) is existing
    assert updates[0][2] == [("provider", "sports")]


def test_arr_history_refiner_skips_a_sports_video(monkeypatch):
    from subtitles.refiners import arr_history

    monkeypatch.setattr(arr_history.settings.general, "enabled_providers", ["avistaz"])
    monkeypatch.setattr(arr_history, "get_history_from_sonarr_api",
                        lambda *args: pytest.fail("Sonarr has no history for a sports event"))
    video = Episode("/sports/UFC/UFC 300.mkv", "UFC", 2024, 5)

    arr_history.refine_from_arr_history(video.name, video)

    assert video.info_url is None


@pytest.fixture
def sports_event_row(memory_session):
    from app.database import TableSportsEvents, TableSportsLeagues

    memory_session.add(TableSportsLeagues(sportarrLeagueId=5, title="UFC", path="/sports/UFC"))
    memory_session.commit()
    memory_session.add(TableSportsEvents(
        id=11, sportarrEventId=300, sportarrLeagueId=5, season=2024, episode=5, title="UFC 300",
        path="/sports/UFC/Season 2024/UFC 300.mkv", format="WEBDL", resolution="1080p", video_codec="h264",
        audio_codec="AAC", file_size=1234))
    memory_session.commit()
    return memory_session


def test_database_refiner_gives_a_sports_video_its_event(monkeypatch, sports_event_row):
    from subtitles.refiners import database as database_refiner

    monkeypatch.setattr(database_refiner, "database", sports_event_row)
    monkeypatch.setattr(database_refiner.path_mappings, "path_replace_reverse", lambda path: f"tv:{path}")
    monkeypatch.setattr(database_refiner.path_mappings, "path_replace_reverse_sports", lambda path: path)
    # guessit reads the folder name as the series, as it did on the test rig.
    video = Episode("/sports/UFC/Season 2024/UFC 300.mkv", "Season", 1, 1)

    database_refiner.refine_from_db(video.name, video)

    assert (video.series, video.title, video.season, video.episode) == ("UFC", "UFC 300", 2024, 5)
    assert video.resolution == "1080p"
    assert (video.sportarrLeagueId, video.sportsEventId) == (5, 11)
    assert not hasattr(video, "sonarrEpisodeId")


def test_ffprobe_refiner_reads_the_sports_cache(monkeypatch, sports_event_row):
    from subtitles.refiners import ffprobe

    calls = []
    monkeypatch.setattr(ffprobe, "database", sports_event_row)
    monkeypatch.setattr(ffprobe.path_mappings, "path_replace_reverse", lambda path: f"tv:{path}")
    monkeypatch.setattr(ffprobe.path_mappings, "path_replace_reverse_sports", lambda path: path)
    monkeypatch.setattr(ffprobe, "parse_video_metadata", lambda **kwargs: calls.append(kwargs) or {
        "ffprobe": {"video": [{"resolution": "720p"}]}, "mediainfo": {}})
    video = Episode("/sports/UFC/Season 2024/UFC 300.mkv", "UFC", 2024, 5)

    ffprobe.refine_from_ffprobe(video.name, video)

    assert calls == [{"file": video.name, "file_size": 1234, "sports_event_id": 11}]
    assert video.resolution == "720p"


def _fallback_search(mocker, minimum_score_sports=95):
    class Video:
        original_path = "/sports/UFC 300.mkv"
        sportarrLeagueId = 5
        sportsEventId = 11

    video = Video()
    settings = mocker.MagicMock()
    settings.general.utf8_encode = False
    settings.general.minimum_score = 90
    settings.general.minimum_score_movie = 70
    settings.general.minimum_score_sports = minimum_score_sports
    settings.general.subzero_mods = ""
    settings.general.chmod_enabled = False
    settings.translator.translate_fallback_enabled = True
    settings.translator.translate_fallback_source_language = "en"
    settings.embeddedsubtitles.prefer_embedded = False

    mocker.patch("subtitles.pool._update_pool", return_value=False)
    mocker.patch("subtitles.download.settings", settings)
    mocker.patch("subtitles.download.get_array_from", return_value=[])
    mocker.patch("subtitles.download.get_profiles_list", return_value={"originalFormat": False, "items": []})
    mocker.patch("subtitles.download._get_pool", return_value=SimpleNamespace(providers=["provider"]))
    mocker.patch("subtitles.download._get_language_obj", return_value=[Language("fra")])
    mocker.patch("subtitles.download._set_forced_providers")
    mocker.patch("subtitles.download.get_video", return_value=video)
    mocker.patch("subtitles.download.get_target_folder", return_value=None)
    mocker.patch("subtitles.download.subliminal")
    return SimpleNamespace(
        video=video,
        scores=mocker.patch("subtitles.download._get_scores", return_value=(0, 100, {})),
        download=mocker.patch("subtitles.download.download_best_subtitles"),
        find_source=mocker.patch("subtitles.download._find_embedded_fallback_source"),
        extract=mocker.patch("subtitles.download._extract_and_translate_embedded_fallback"),
        translate=mocker.patch("subtitles.download._translate_fallback_source"),
        save=mocker.patch("subtitles.download.save_subtitles"),
    )


def _run_sports_search():
    from subtitles.download import generate_subtitles

    return list(generate_subtitles(path="/sports/UFC 300.mkv", languages=[("fr", "False", "False")],
                                   audio_language="English", sceneName=None, title="UFC", media_type="sports",
                                   profile_id=1, job_id=99))


def test_sports_search_uses_the_sports_minimum_score(mocker):
    ctx = _fallback_search(mocker, minimum_score_sports=95)
    ctx.download.return_value = {ctx.video: []}
    ctx.find_source.return_value = None

    _run_sports_search()

    ctx.scores.assert_called_once_with("sports", 70, 95)


def test_sports_minimum_score_setting_exists():
    from app.config import settings

    assert isinstance(settings.general.minimum_score_sports, int)
    assert 0 <= settings.general.minimum_score_sports <= 100


def test_sports_translation_fallback_keeps_the_sports_ids(mocker):
    ctx = _fallback_search(mocker)
    ctx.download.side_effect = [
        {ctx.video: []},
        {ctx.video: [SimpleNamespace(format="srt", mods=None)]},
    ]
    ctx.save.return_value = [
        SimpleNamespace(language=Language("eng"), storage_path="/sports/UFC 300.en.srt", matches=set())]

    _run_sports_search()

    kwargs = ctx.translate.call_args.kwargs
    assert kwargs["media_type"] == "sports"
    assert (kwargs["sportarr_league_id"], kwargs["sports_event_id"]) == (5, 11)
    assert kwargs["radarr_id"] is None


def test_sports_embedded_translation_fallback_keeps_the_sports_ids(mocker):
    ctx = _fallback_search(mocker)
    ctx.download.side_effect = [{ctx.video: []}, {ctx.video: []}]
    ctx.find_source.return_value = {"id": 7, "code3": "eng", "embedded_track_id": 3}

    _run_sports_search()

    ctx.find_source.assert_called_once_with(ctx.video, "en", "sports")
    kwargs = ctx.extract.call_args.kwargs
    assert kwargs["media_type"] == "sports"
    assert (kwargs["sportarr_league_id"], kwargs["sports_event_id"]) == (5, 11)


def test_sports_embedded_fallback_source_reads_the_sports_subtitles(mocker):
    from subtitles.download import _find_embedded_fallback_source

    get_sports_subtitles = mocker.patch("subtitles.download.get_sports_subtitles", return_value=[
        {"id": 4, "code3": "eng", "embedded_track_id": 2}])
    mocker.patch("subtitles.download.get_subtitles", side_effect=AssertionError("not a movie"))

    result = _find_embedded_fallback_source(SimpleNamespace(sportsEventId=11), "en", "sports")

    assert result["id"] == 4
    get_sports_subtitles.assert_called_once_with(sports_event_id=11)


def test_sports_translated_fallback_is_indexed_as_sports(mocker):
    from subtitles.download import _translate_fallback_source

    translate = mocker.patch("subtitles.download.translate_subtitles_file", return_value="/sports/a.fr.srt")
    store_sports = mocker.patch("subtitles.indexer.sports.store_subtitles_sports")
    store_movie = mocker.patch("subtitles.indexer.movies.store_subtitles_movie")

    _translate_fallback_source(video_path="/sports/a.mkv", source_srt_file="/sports/a.en.srt", from_lang="en",
                               to_lang="fr", forced=False, hi=False, media_type="sports", sonarr_series_id=None,
                               sonarr_episode_id=None, radarr_id=None, original_format=False, job_id=1,
                               sportarr_league_id=5, sports_event_id=11)

    assert translate.call_args.kwargs["sports_event_id"] == 11
    store_sports.assert_called_once_with(11)
    store_movie.assert_not_called()


def test_sports_translation_result_uses_the_sports_path_mapping(monkeypatch):
    from subtitles.tools.translate.core import translator_utils

    monkeypatch.setattr(translator_utils.path_mappings, "path_replace_reverse_sports", lambda path: f"sports:{path}")
    monkeypatch.setattr(translator_utils.path_mappings, "path_replace_reverse_movie", lambda path: f"movie:{path}")

    result = translator_utils.create_process_result("done", "/sports/a.mkv", "fr", False, False,
                                                    "/sports/a.fr.srt", "sports")

    assert (result.path, result.subs_path) == ("sports:/sports/a.mkv", "sports:/sports/a.fr.srt")


def test_sports_translation_is_logged_to_sports_history(monkeypatch, tmp_path):
    from subtitles.tools.translate.services import google_translator

    logged = []
    source = tmp_path / "a.en.srt"
    source.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello\n")
    monkeypatch.setattr(google_translator, "history_log_sports", lambda **kwargs: logged.append(kwargs))
    monkeypatch.setattr(google_translator, "history_log_movie", lambda **kwargs: pytest.fail("not a movie"))
    monkeypatch.setattr(google_translator, "add_translator_info", lambda *args: None)
    monkeypatch.setattr(google_translator, "create_process_result", lambda *args: "result")
    monkeypatch.setattr(google_translator.jobs_queue, "update_job_progress", lambda **kwargs: None)
    monkeypatch.setattr(google_translator.jobs_queue, "raise_if_cancel_requested", lambda job_id: None)
    monkeypatch.setattr(google_translator.GoogleTranslatorService, "_translate_text",
                        lambda self, line, job_id: line.upper())

    service = google_translator.GoogleTranslatorService(
        source_srt_file=str(source), dest_srt_file=str(tmp_path / "a.fr.srt"), lang_obj=Language("fra"),
        to_lang="fra", from_lang="en", media_type="sports", video_path=str(tmp_path / "a.mkv"),
        orig_to_lang="fr", forced=False, hi=False, sonarr_series_id=None, sonarr_episode_id=None, radarr_id=None,
        sportarr_league_id=5, sports_event_id=11)
    service.translate(job_id=1)

    assert logged == [{"action": 6, "sportarr_league_id": 5, "sports_event_id": 11, "result": "result"}]
