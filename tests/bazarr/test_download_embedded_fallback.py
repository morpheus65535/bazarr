from types import SimpleNamespace

from subzero.language import Language

from subtitles.download import (
    _extract_and_translate_embedded_fallback,
    _find_embedded_fallback_source,
    generate_subtitles,
)


def test_find_embedded_fallback_source_selects_matching_indexed_embedded_track(mocker):
    video = SimpleNamespace(sonarrEpisodeId=99)
    get_subtitles = mocker.patch(
        "subtitles.download.get_subtitles",
        return_value=[
            {"id": 1, "code3": "eng", "embedded_track_id": None},
            {"id": 2, "code3": "fra", "embedded_track_id": 4},
            {"id": 3, "code3": "eng", "embedded_track_id": 7},
        ],
    )

    result = _find_embedded_fallback_source(video, "en", "series")

    assert result["id"] == 3
    get_subtitles.assert_called_once_with(sonarr_episode_id=99)


def test_find_embedded_fallback_source_uses_movie_id(mocker):
    video = SimpleNamespace(radarrId=42)
    get_subtitles = mocker.patch(
        "subtitles.download.get_subtitles",
        return_value=[{"id": 5, "code3": "eng", "embedded_track_id": 8}],
    )

    result = _find_embedded_fallback_source(video, "en", "movie")

    assert result["id"] == 5
    get_subtitles.assert_called_once_with(radarr_id=42)


def test_find_embedded_fallback_source_ignores_unindexed_or_other_language_tracks(mocker):
    video = SimpleNamespace(radarrId=42)
    mocker.patch(
        "subtitles.download.get_subtitles",
        return_value=[
            {"id": 1, "code3": "eng", "embedded_track_id": None},
            {"id": 2, "code3": "fra", "embedded_track_id": 7},
        ],
    )

    assert _find_embedded_fallback_source(video, "en", "movie") is None


def test_embedded_fallback_uses_shared_extractor_then_translates(mocker):
    extract = mocker.patch(
        "subtitles.embedded.extract_embedded_subtitle",
        return_value="/media/movie.en.extracted.srt",
    )
    translate = mocker.patch(
        "subtitles.download._translate_fallback_source",
        return_value="/media/movie.fr.srt",
    )

    result = _extract_and_translate_embedded_fallback(
        subtitles_id=7,
        video_path="/media/movie.mkv",
        from_lang="en",
        to_lang="fr",
        forced=False,
        hi=False,
        media_type="movie",
        sonarr_series_id=None,
        sonarr_episode_id=None,
        radarr_id=42,
        original_format=False,
        job_id=123,
    )

    assert result == "/media/movie.fr.srt"
    extract.assert_called_once_with(
        subtitles_id=7,
        media_type="movie",
        job_id=123,
        filename_suffix=".extracted",
    )
    translate.assert_called_once_with(
        video_path="/media/movie.mkv",
        source_srt_file="/media/movie.en.extracted.srt",
        from_lang="en",
        to_lang="fr",
        forced=False,
        hi=False,
        media_type="movie",
        sonarr_series_id=None,
        sonarr_episode_id=None,
        radarr_id=42,
        original_format=False,
        job_id=123,
    )


def test_embedded_fallback_without_job_id_queues_combined_operation(mocker):
    enqueue = mocker.patch("subtitles.download.jobs_queue.add_job_from_function", return_value=1)
    extract = mocker.patch("subtitles.embedded.extract_embedded_subtitle")
    translate = mocker.patch("subtitles.download._translate_fallback_source")

    result = _extract_and_translate_embedded_fallback(
        subtitles_id=7,
        video_path="/media/movie.mkv",
        from_lang="en",
        to_lang="fr",
        forced=False,
        hi=False,
        media_type="movie",
        sonarr_series_id=None,
        sonarr_episode_id=None,
        radarr_id=42,
        original_format=False,
    )

    assert result is True
    enqueue.assert_called_once()
    extract.assert_not_called()
    translate.assert_not_called()


def test_generate_subtitles_uses_embedded_fallback_when_providers_miss(mocker):
    class Video:
        original_path = "/media/Movie.mkv"
        radarrId = 42
        sonarrEpisodeId = None
        sonarrSeriesId = None

    video = Video()
    pool = SimpleNamespace(providers=["test-provider"])
    settings = mocker.MagicMock()
    settings.general.utf8_encode = False
    settings.general.minimum_score = 90
    settings.general.minimum_score_movie = 70
    settings.general.subzero_mods = ""
    settings.translator.translate_fallback_enabled = True
    settings.translator.translate_fallback_source_language = "en"
    settings.embeddedsubtitles.prefer_embedded = False

    mocker.patch("subtitles.pool._update_pool", return_value=False)
    mocker.patch("subtitles.download.settings", settings)
    mocker.patch("subtitles.download.get_array_from", return_value=[])
    mocker.patch("subtitles.download.get_profiles_list", return_value={"originalFormat": False, "items": []})
    mocker.patch("subtitles.download._get_pool", return_value=pool)
    mocker.patch("subtitles.download._get_language_obj", return_value={Language("fra")})
    mocker.patch("subtitles.download._set_forced_providers")
    mocker.patch("subtitles.download._get_scores", return_value=(0, 100, {}))
    mocker.patch("subtitles.download.get_video", return_value=video)
    mocker.patch("subtitles.download.download_best_subtitles", side_effect=[{video: []}, {video: []}])
    find_source = mocker.patch(
        "subtitles.download._find_embedded_fallback_source",
        return_value={"id": 7, "code3": "eng", "embedded_track_id": 3},
    )
    extract_and_translate = mocker.patch(
        "subtitles.download._extract_and_translate_embedded_fallback",
        return_value="/media/Movie.fr.srt",
    )
    mocker.patch("subtitles.download.subliminal")

    list(generate_subtitles(
        path="/media/Movie.mkv",
        languages=[("fr", "False", "False")],
        audio_language="English",
        sceneName=None,
        title="Movie",
        media_type="movie",
        profile_id=1,
        job_id=99,
    ))

    find_source.assert_called_once_with(video, "en", "movie")
    extract_and_translate.assert_called_once_with(
        subtitles_id=7,
        video_path="/media/Movie.mkv",
        from_lang="en",
        to_lang="fr",
        forced=False,
        hi=False,
        media_type="movie",
        sonarr_series_id=None,
        sonarr_episode_id=None,
        radarr_id=42,
        original_format=False,
        job_id=99,
    )
