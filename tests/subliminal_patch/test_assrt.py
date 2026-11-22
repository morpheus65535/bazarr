from subliminal_patch.core import Movie, SZProviderPool
from subliminal_patch.core_persistent import download_best_subtitles
from subliminal_patch.providers.assrt import AssrtProvider
from subliminal_patch.score import MAX_SCORES
from subzero.language import Language


ASSRT_BASE_URL = "https://api.assrt.net/v1"
AUTO_FILE_URL = "https://files.assrt.net/download/602333"
AUTO_VALID_SRT = b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello subtitle\r\n\r\n"
# Bazarr's default general.minimum_score_movie is 70% of MAX_SCORES['movie'].
DEFAULT_MOVIE_MIN_SCORE = int(MAX_SCORES["movie"] * 70 / 100)


def _automatic_pool(provider):
    pool = SZProviderPool(providers={"assrt"})
    pool.initialized_providers["assrt"] = provider
    return pool


def _automatic_video():
    # Keep title/year/source derived from a natural release; no title aliases.
    return Movie(
        "Backrooms.2026.1080p.WEB-DL.mkv",
        "Backrooms",
        year=2026,
        source="Web",
        resolution="1080p",
    )


def test_list_subtitles_with_current_search_schema(mocker, requests_mock):
    """Current Assrt results use m_langn, sub_name, and fileid."""
    mocker.patch("subliminal_patch.providers.assrt.sleep")
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/search",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "fileid": 602333,
                        "sub_name": "[收藏级] 后室【中英双语注释+特效 蒙太奇字幕组】Backrooms.2026.匹配1小时50分WEB版.V2.zip",
                        "m_lang": "简体中文",
                        "m_langn": ["langchs"],
                    }
                ]
            },
        },
    )
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/detail",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "filelist": [],
                        "url": "https://files.assrt.net/download/602333",
                    }
                ]
            },
        },
    )

    provider = AssrtProvider(token="fixture-token-not-real")
    provider.max_request_per_minute = 60
    try:
        video = Movie("Backrooms.2026.mkv", "后室", year=2026)
        subtitles = provider.list_subtitles(video, {Language("zho", "CN")})

        assert len(subtitles) == 1
        subtitle = subtitles[0]
        assert subtitle.language == Language("zho", "CN")
        assert subtitle.id == 602333
        assert subtitle.video_name == (
            "[收藏级] 后室【中英双语注释+特效 蒙太奇字幕组】"
            "Backrooms.2026.匹配1小时50分WEB版.V2.zip"
        )
        assert subtitle.download_link == "https://files.assrt.net/download/602333"
        assert requests_mock.request_history[1].qs["id"] == ["602333"]
    finally:
        provider.terminate()


def test_list_subtitles_with_legacy_search_schema(mocker, requests_mock):
    mocker.patch("subliminal_patch.providers.assrt.sleep")
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/search",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "id": 123456,
                        "videoname": "Backrooms.2026.WEB-DL",
                        "lang": {"langlist": {"langchs": True, "langeng": False}},
                    }
                ]
            },
        },
    )

    provider = AssrtProvider(token="fixture-token-not-real")
    provider.max_request_per_minute = 60
    try:
        subtitles = provider.list_subtitles(
            Movie("Backrooms.2026.mkv", "后室", year=2026),
            {Language("zho", "CN")},
        )

        assert len(subtitles) == 1
        assert subtitles[0].id == 123456
        assert subtitles[0].language == Language("zho", "CN")
        assert subtitles[0].video_name == "Backrooms.2026.WEB-DL"
    finally:
        provider.terminate()


def test_current_schema_through_automatic_consumer_downloads_valid_subtitle(mocker, requests_mock):
    """Exercise provider, pool, score/selection and the actual download validator."""
    mocker.patch("subliminal_patch.providers.assrt.sleep")
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/search",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "fileid": 602333,
                        "sub_name": "Backrooms.2026.WEB-DL",
                        "m_langn": ["langchs"],
                    }
                ]
            },
        },
    )
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/detail",
        json={
            "status": 0,
            "sub": {"subs": [{"filelist": [], "url": AUTO_FILE_URL}]},
        },
    )
    requests_mock.get(AUTO_FILE_URL, content=AUTO_VALID_SRT)

    provider = AssrtProvider(token="fixture-token-not-real")
    provider.max_request_per_minute = 60
    video = _automatic_video()
    language = Language("zho", "CN")
    try:
        selected_by_video = download_best_subtitles(
            videos={video},
            languages={language},
            pool_instance=_automatic_pool(provider),
            min_score=DEFAULT_MOVIE_MIN_SCORE,
        )
        selected = selected_by_video[video]
        assert len(selected) == 1
        subtitle = selected[0]
        assert subtitle.id == 602333
        assert subtitle.language == language
        assert subtitle.score >= DEFAULT_MOVIE_MIN_SCORE
        assert subtitle.is_valid()
        assert subtitle.content == AUTO_VALID_SRT.replace(b"\r\n", b"\n")
        assert requests_mock.request_history[1].qs["id"] == ["602333"]
        assert requests_mock.request_history[2].url == AUTO_FILE_URL
    finally:
        provider.terminate()


def test_legacy_schema_through_automatic_consumer_still_downloads(mocker, requests_mock):
    mocker.patch("subliminal_patch.providers.assrt.sleep")
    file_url = "https://files.assrt.net/download/123456"
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/search",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "id": 123456,
                        "videoname": "Backrooms.2026.WEB-DL",
                        "lang": {"langlist": {"langchs": True}},
                    }
                ]
            },
        },
    )
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/detail",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "filelist": [],
                        "url": file_url,
                    }
                ]
            },
        },
    )
    requests_mock.get(file_url, content=AUTO_VALID_SRT)

    provider = AssrtProvider(token="fixture-token-not-real")
    provider.max_request_per_minute = 60
    video = _automatic_video()
    language = Language("zho", "CN")
    try:
        selected_by_video = download_best_subtitles(
            videos={video},
            languages={language},
            pool_instance=_automatic_pool(provider),
            min_score=DEFAULT_MOVIE_MIN_SCORE,
        )
        selected = selected_by_video[video]
        assert len(selected) == 1
        assert selected[0].id == 123456
        assert selected[0].is_valid()
        assert requests_mock.request_history[1].qs["id"] == ["123456"]
    finally:
        provider.terminate()


def test_current_schema_wrong_title_is_rejected_by_automatic_score_gate(mocker, requests_mock):
    mocker.patch("subliminal_patch.providers.assrt.sleep")
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/search",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "fileid": 999001,
                        "sub_name": "Different.Movie.2026.WEB-DL",
                        "m_langn": ["langchs"],
                    }
                ]
            },
        },
    )

    provider = AssrtProvider(token="fixture-token-not-real")
    provider.max_request_per_minute = 60
    video = _automatic_video()
    try:
        selected_by_video = download_best_subtitles(
            videos={video},
            languages={Language("zho", "CN")},
            pool_instance=_automatic_pool(provider),
            min_score=DEFAULT_MOVIE_MIN_SCORE,
        )
        assert selected_by_video[video] == []
        assert len(requests_mock.request_history) == 1
        assert requests_mock.request_history[0].path_url.startswith("/v1/sub/search")
    finally:
        provider.terminate()


def test_current_schema_unresolvable_fileid_is_not_downloaded(mocker, requests_mock):
    mocker.patch("subliminal_patch.providers.assrt.sleep")
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/search",
        json={
            "status": 0,
            "sub": {
                "subs": [
                    {
                        "fileid": 999001,
                        "sub_name": "Backrooms.2026.WEB-DL",
                        "m_langn": ["langchs"],
                    }
                ]
            },
        },
    )
    requests_mock.get(
        f"{ASSRT_BASE_URL}/sub/detail",
        json={"status": 0, "sub": {"subs": []}},
    )

    provider = AssrtProvider(token="fixture-token-not-real")
    provider.max_request_per_minute = 60
    video = _automatic_video()
    try:
        selected_by_video = download_best_subtitles(
            videos={video},
            languages={Language("zho", "CN")},
            pool_instance=_automatic_pool(provider),
            min_score=DEFAULT_MOVIE_MIN_SCORE,
        )
        assert selected_by_video[video] == []
        assert len(requests_mock.request_history) == 2
        assert requests_mock.request_history[1].qs["id"] == ["999001"]
    finally:
        provider.terminate()
