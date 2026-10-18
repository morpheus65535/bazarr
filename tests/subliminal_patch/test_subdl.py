import os

import pytest
from subliminal.exceptions import ServiceUnavailable
from subliminal_patch.providers.subdl import SubdlProvider
from subliminal_patch.providers.subdl import SubdlSubtitle
from subliminal_patch.core import Episode
from subzero.language import Language


@pytest.fixture(scope="session")
def provider():
    with SubdlProvider(os.environ["SUBDL_TOKEN"]) as provider:
        yield provider


SEARCH_URL = "https://api.subdl.com/api/v1/subtitles"
TRANSLATE_URL = "https://api.subdl.com/api/v1/pro/translate/subtitles"
JOB_URL = "https://api.subdl.com/api/v1/pro/translate/jobs/job1"
DOWNLOAD_URL = "https://api.subdl.com/api/v1/pro/translate/jobs/job1/download"

# Release names match the "dune" movie fixture so the matching source wins.
MATCHING_RELEASE = "Dune.2021.1080p.WEBRip.DD5.1.x264-SHITBOX"
OTHER_RELEASE = "Dune.2021.720p.BluRay.x264-OTHER"


def search_response(translation=None, subtitles=None):
    body = {
        "status": True,
        "results": [
            {
                "imdb_id": "tt1160419",
                "tmdb_id": 438631,
                "type": "movie",
                "name": "Dune",
                "sd_id": 123456,
                "year": 2021,
            }
        ],
        "subtitles": subtitles or [],
    }
    if translation is not None:
        body["translation"] = translation
    return body


def entitled_translation(sources=None, missing=None):
    return {
        "entitled": True,
        "quota_remaining": 42,
        "quota_reset_at": "2026-08-01T00:00:00.000Z",
        "missing_languages": missing or ["FA"],
        "sources": sources
        if sources is not None
        else [
            {
                "n_id": "src2",
                "language": "EN",
                "hi": False,
                "releases": [OTHER_RELEASE],
            },
            {
                "n_id": "src1",
                "language": "EN",
                "hi": False,
                "releases": [MATCHING_RELEASE],
            },
        ],
    }


@pytest.fixture
def ai_provider():
    with SubdlProvider("fake-key", ai_translate=True) as provider:
        yield provider


def test_ai_candidate_synthesized(ai_provider, movies, requests_mock):
    requests_mock.get(SEARCH_URL, json=search_response(entitled_translation()))

    fa = Language("fas")
    subtitles = ai_provider.list_subtitles(movies["dune"], {fa})

    assert len(subtitles) == 1
    candidate = subtitles[0]
    assert candidate.is_ai_translation
    assert candidate.language == fa
    # The source whose releases match the video must win, not the first one.
    assert candidate.ai_source_n_id == "src1"
    assert candidate.ai_target_language == "FA"
    assert candidate.release_info.startswith("AI translation (SubDL) from EN")
    assert candidate.uploader == "SubDL AI"
    assert "title" in candidate.matches


def test_ai_candidate_requires_setting(movies, requests_mock):
    requests_mock.get(SEARCH_URL, json=search_response(entitled_translation()))

    with SubdlProvider("fake-key", ai_translate=False) as provider:
        assert provider.list_subtitles(movies["dune"], {Language("fas")}) == []


def test_no_candidate_when_not_entitled(ai_provider, movies, requests_mock):
    translation = {
        "entitled": False,
        "quota_remaining": 0,
        "quota_reset_at": None,
        "missing_languages": ["FA"],
        "upgrade_url": "https://subdl.com/pro?ref=bazarr",
    }
    requests_mock.get(SEARCH_URL, json=search_response(translation))

    assert ai_provider.list_subtitles(movies["dune"], {Language("fas")}) == []


def test_no_candidate_when_quota_exhausted(ai_provider, movies, requests_mock):
    translation = {
        "entitled": True,
        "quota_remaining": 0,
        "quota_reset_at": "2026-08-01T00:00:00.000Z",
        "missing_languages": ["FA"],
    }
    requests_mock.get(SEARCH_URL, json=search_response(translation))

    assert ai_provider.list_subtitles(movies["dune"], {Language("fas")}) == []


def test_no_candidate_when_language_already_found(ai_provider, movies, requests_mock):
    existing = {
        "url": "/subtitle/1-1.zip",
        "name": "dune-fa.zip",
        "language": "FA",
        "subtitlePage": "/s/info/abc",
        "releases": [MATCHING_RELEASE],
        "author": "someone",
    }
    requests_mock.get(
        SEARCH_URL,
        json=search_response(entitled_translation(), subtitles=[existing]),
    )

    subtitles = ai_provider.list_subtitles(movies["dune"], {Language("fas")})

    assert len(subtitles) == 1
    assert not subtitles[0].is_ai_translation


def test_graceful_without_translation_block(ai_provider, movies, requests_mock):
    requests_mock.get(SEARCH_URL, json=search_response())

    assert ai_provider.list_subtitles(movies["dune"], {Language("fas")}) == []


def test_include_ai_translated_filter(movies, requests_mock):
    item = {
        "url": "/subtitle/1-1.zip",
        "name": "dune-fa-ai.zip",
        "language": "FA",
        "subtitlePage": "/s/info/abc",
        "releases": [MATCHING_RELEASE],
        "author": "someone",
        "ai_translated": True,
    }
    requests_mock.get(SEARCH_URL, json=search_response(None, subtitles=[item]))

    with SubdlProvider("fake-key", include_ai_translated=False) as provider:
        assert provider.list_subtitles(movies["dune"], {Language("fas")}) == []

    with SubdlProvider("fake-key", include_ai_translated=True) as provider:
        subtitles = provider.list_subtitles(movies["dune"], {Language("fas")})
        assert len(subtitles) == 1
        assert "AI translated" in subtitles[0].uploader


def ai_candidate():
    return SubdlSubtitle(
        language=Language("fas"),
        forced=False,
        hearing_impaired=False,
        page_link="https://subdl.com/pro?ref=bazarr",
        download_link=None,
        file_id="ai:src1:FA",
        release_names=[MATCHING_RELEASE],
        uploader="SubDL AI",
        season=None,
        episode=None,
        is_ai_translation=True,
        ai_source_n_id="src1",
        ai_source_language="EN",
        ai_target_language="FA",
    )


def test_download_ai_translation(requests_mock, mocker):
    mocker.patch("time.sleep")
    requests_mock.post(
        TRANSLATE_URL,
        status_code=202,
        json={
            "status": True,
            "request_id": "job1",
            "job": {"status": "queued", "download_ready": False},
            "estimated_duration_ms": 30000,
        },
    )
    requests_mock.get(
        JOB_URL,
        json={"job": {"status": "translated", "download_ready": True}},
    )
    requests_mock.get(
        DOWNLOAD_URL,
        content=b"1\n00:00:01,000 --> 00:00:02,000\nsalam\n",
    )

    sub = ai_candidate()
    with SubdlProvider("fake-key", ai_translate=True) as provider:
        provider.download_subtitle(sub)

    assert sub.content is not None
    assert b"salam" in sub.content


def test_download_ai_translation_reused_job(requests_mock, mocker):
    mocker.patch("time.sleep")
    requests_mock.post(
        TRANSLATE_URL,
        status_code=200,
        json={
            "status": True,
            "request_id": "job1",
            "reused": True,
            "job": {"status": "published", "download_ready": True},
        },
    )
    requests_mock.get(DOWNLOAD_URL, content=b"1\n00:00:01,000 --> 00:00:02,000\nsalam\n")

    sub = ai_candidate()
    with SubdlProvider("fake-key", ai_translate=True) as provider:
        provider.download_subtitle(sub)

    assert sub.content is not None


def test_download_ai_translation_quota_exhausted_never_raises(requests_mock):
    requests_mock.post(
        TRANSLATE_URL,
        status_code=429,
        json={
            "status": False,
            "error": "translation_quota_exhausted",
            "message": "Monthly translation quota exhausted",
        },
    )

    sub = ai_candidate()
    with SubdlProvider("fake-key", ai_translate=True) as provider:
        # Must not raise DownloadLimitExceeded (that would throttle ALL subdl
        # downloads until midnight) — just fail this one candidate.
        provider.download_subtitle(sub)

    assert sub.content is None


def test_search_402_raises_provider_error(requests_mock):
    from subliminal.exceptions import ProviderError

    requests_mock.get(
        SEARCH_URL,
        status_code=402,
        json={
            "status": False,
            "error": "paid_api_required",
            "message": "Active paid API subscription required",
        },
    )

    with SubdlProvider("fake-key") as provider:
        with pytest.raises(ProviderError, match="Active paid API subscription required"):
            provider.checked(
                lambda: provider.session.get(SEARCH_URL, timeout=30))


def test_download_ai_translation_job_failure(requests_mock, mocker):
    mocker.patch("time.sleep")
    requests_mock.post(
        TRANSLATE_URL,
        status_code=202,
        json={
            "status": True,
            "request_id": "job1",
            "job": {"status": "queued", "download_ready": False},
            "estimated_duration_ms": 30000,
        },
    )
    requests_mock.get(JOB_URL, json={"job": {"status": "failed", "error": "boom"}})

    sub = ai_candidate()
    with SubdlProvider("fake-key", ai_translate=True) as provider:
        provider.download_subtitle(sub)

    assert sub.content is None


def test_is_hi_marker_in_comment():
    # An HI/SDH marker in the uploader comment flags the subtitle as hearing impaired.
    item = {
        "comment": "SDH version",
        "name": "dune-en.zip",
        "releases": [MATCHING_RELEASE],
    }
    assert SubdlProvider._is_hi(item) is True


def test_is_hi_marker_in_release_name():
    # An HI/SDH marker present only in a release name must be detected too. This
    # used to be a dead branch: the release names were nested as a list inside
    # hi_keys, so `x in key` did exact list membership instead of the intended
    # substring scan and never matched a real release name.
    item = {
        "comment": "",
        "name": "dune-en.zip",
        "releases": ["Dune.2021.1080p.WEBRip.DD5.1.x264.SDH-SHITBOX"],
    }
    assert SubdlProvider._is_hi(item) is True


def test_is_hi_negative():
    # No HI markers anywhere: not hearing impaired.
    item = {
        "comment": "great subtitle",
        "name": "dune-en.zip",
        "releases": [MATCHING_RELEASE, OTHER_RELEASE],
    }
    assert SubdlProvider._is_hi(item) is False


def test_list_subtitles_movie(provider, movies, languages):
    for sub in provider.list_subtitles(movies["dune"], {languages["en"]}):
        assert sub.language == languages["en"]


def test_download_subtitle(provider, languages):
    data = {
        "language": languages["en"],
        "forced": False,
        "hearing_impaired": False,
        "page_link": "https://subdl.com/s/info/ebC6BrLCOC",
        "download_link": "/subtitle/2808552-2770424.zip",
        "file_id": "SUBDL::dune-2021-2770424.zip",
        "release_names": ["Dune Part 1 WebDl"],
        "uploader": "makoto77",
        "season": 0,
        "episode": None,
    }

    sub = SubdlSubtitle(**data)
    provider.download_subtitle(sub)

    assert sub.is_valid()


# --- 2026-08 fixes: candidate suppression, default-toggle blind spot, unpack
# cross-check, per-HI-class sources, quota back-off, Traditional Chinese ------


def episode_search_response(translation=None, subtitles=None):
    body = {
        "status": True,
        "results": [
            {
                "imdb_id": "tt0944947",
                "type": "tv",
                "name": "Game of Thrones",
                "sd_id": 1,
                "year": 2011,
            }
        ],
        "subtitles": subtitles or [],
    }
    if translation is not None:
        body["translation"] = translation
    return body


def test_other_episodes_row_does_not_suppress_ai_candidate(
    ai_provider, episodes, requests_mock
):
    # The season-only search returns a Farsi row for a DIFFERENT episode.
    # bazarr will reject that row on its episode guard, so it must not count
    # as "this language already exists" — that suppression turned the feature
    # off for a whole season as soon as one episode had the language.
    other_episode_row = {
        "url": "/subtitle/9-9.zip",
        "name": "Game.of.Thrones.S03E01.720p.WEB-DL.fa.zip",
        "language": "FA",
        "subtitlePage": "/s/info/other",
        "releases": ["Game.of.Thrones.S03E01.720p.WEB-DL.DD5.1.H.264-NTb"],
        "author": "someone",
        "season": 3,
        "episode": 1,
    }
    requests_mock.get(
        SEARCH_URL,
        json=episode_search_response(
            entitled_translation(
                sources=[
                    {
                        "n_id": "srcE10",
                        "language": "EN",
                        "hi": False,
                        "releases": [
                            "Game.of.Thrones.S03E10.Mhysa.720p.WEB-DL.DD5.1.H.264-NTb"
                        ],
                    }
                ]
            ),
            subtitles=[other_episode_row],
        ),
    )

    subtitles = ai_provider.list_subtitles(episodes["got_s03e10"], {Language("fas")})

    candidates = [sub for sub in subtitles if sub.is_ai_translation]
    assert len(candidates) == 1
    assert candidates[0].ai_source_n_id == "srcE10"


def test_same_episode_row_still_suppresses_ai_candidate(
    ai_provider, episodes, requests_mock
):
    same_episode_row = {
        "url": "/subtitle/9-9.zip",
        "name": "Game.of.Thrones.S03E10.720p.WEB-DL.fa.zip",
        "language": "FA",
        "subtitlePage": "/s/info/same",
        "releases": ["Game.of.Thrones.S03E10.Mhysa.720p.WEB-DL.DD5.1.H.264-NTb"],
        "author": "someone",
        "season": 3,
        "episode": 10,
    }
    requests_mock.get(
        SEARCH_URL,
        json=episode_search_response(
            entitled_translation(), subtitles=[same_episode_row]
        ),
    )

    subtitles = ai_provider.list_subtitles(episodes["got_s03e10"], {Language("fas")})

    assert [sub for sub in subtitles if sub.is_ai_translation] == []


def test_ai_translate_implies_including_ai_rows(movies, requests_mock):
    # A user who asked SubDL to produce machine translations accepts machine
    # translations. Without this, the default include_ai_translated=False hid
    # a freshly published translation from the account that requested it.
    item = {
        "url": "/subtitle/1-1.zip",
        "name": "dune-fa-ai.zip",
        "language": "FA",
        "subtitlePage": "/s/info/abc",
        "releases": [MATCHING_RELEASE],
        "author": "someone",
        "ai_translated": True,
    }
    requests_mock.get(SEARCH_URL, json=search_response(None, subtitles=[item]))

    with SubdlProvider(
        "fake-key", ai_translate=True, include_ai_translated=False
    ) as provider:
        subtitles = provider.list_subtitles(movies["dune"], {Language("fas")})

    assert len(subtitles) == 1
    assert "AI translated" in subtitles[0].uploader


def test_select_unpack_entry_rejects_contradicted_claim():
    # Production data: the server claimed "03 ...And the Bag's in the River"
    # was episode 1. The name says otherwise, so the entry must be skipped
    # (falling back to client-side archive extraction) rather than served as
    # the wrong episode.
    files = [
        {"name": "03 ...And the Bag's in the River.en.srt", "episode": 1},
        {"name": "01 Pilot.en.srt", "episode": 0},
    ]
    picked = SubdlProvider._select_unpack_entry(files, target_episode=1)
    assert picked is not None
    assert picked["name"] == "01 Pilot.en.srt"


def test_select_unpack_entry_uses_name_when_server_has_nothing():
    files = [{"name": "05 Gray Matter.en.srt", "episode": 0}]
    picked = SubdlProvider._select_unpack_entry(files, target_episode=5)
    assert picked is not None
    assert picked["name"] == "05 Gray Matter.en.srt"


def test_select_unpack_entry_prefers_matching_hi_class():
    files = [
        {"name": "Show.S01E05.SDH.srt", "episode": 5, "hi": True},
        {"name": "Show.S01E05.srt", "episode": 5, "hi": False},
    ]
    non_hi = SubdlProvider._select_unpack_entry(files, target_episode=5, prefer_hi=False)
    hi = SubdlProvider._select_unpack_entry(files, target_episode=5, prefer_hi=True)
    assert non_hi["name"] == "Show.S01E05.srt"
    assert hi["name"] == "Show.S01E05.SDH.srt"


def test_select_unpack_entry_none_when_nothing_matches():
    files = [{"name": "02 Other.en.srt", "episode": 2}]
    assert SubdlProvider._select_unpack_entry(files, target_episode=7) is None


def test_hi_source_does_not_silence_non_hi_candidate(ai_provider, movies, requests_mock):
    # The HI source matches the video release best; the non-HI candidate must
    # still be offered, from the best NON-HI source.
    translation = entitled_translation(
        sources=[
            {"n_id": "srcHI", "language": "EN", "hi": True, "releases": [MATCHING_RELEASE]},
            {"n_id": "srcNonHI", "language": "EN", "hi": False, "releases": [OTHER_RELEASE]},
        ]
    )
    requests_mock.get(SEARCH_URL, json=search_response(translation))

    subtitles = ai_provider.list_subtitles(movies["dune"], {Language("fas")})

    assert len(subtitles) == 1
    candidate = subtitles[0]
    assert candidate.ai_source_n_id == "srcNonHI"
    assert candidate.hearing_impaired is False


def test_quota_exhausted_pauses_candidates(movies, requests_mock, mocker):
    requests_mock.get(SEARCH_URL, json=search_response(entitled_translation()))
    requests_mock.post(
        TRANSLATE_URL,
        status_code=429,
        json={"status": False, "error": "translation_quota_exhausted"},
    )

    with SubdlProvider("fake-key", ai_translate=True) as provider:
        first = provider.list_subtitles(movies["dune"], {Language("fas")})
        assert len(first) == 1

        provider.download_subtitle(first[0])
        assert first[0].content is None

        # The server said the quota is gone: no more candidates for a while.
        assert provider.list_subtitles(movies["dune"], {Language("fas")}) == []


def test_traditional_chinese_reaches_subdl(movies, requests_mock):
    # bazarr's Chinese Traditional is zho-TW. The converter used to key ZH_BG
    # on script Hant, so this raised and subdl was skipped for the profile.
    item = {
        "url": "/subtitle/1-1.zip",
        "name": "dune-zh-bg.zip",
        "language": "ZH_BG",
        "subtitlePage": "/s/info/zht",
        "releases": [MATCHING_RELEASE],
        "author": "someone",
    }
    requests_mock.get(SEARCH_URL, json=search_response(None, subtitles=[item]))

    zht = Language("zho", "TW")
    with SubdlProvider("fake-key") as provider:
        subtitles = provider.list_subtitles(movies["dune"], {zht})

    assert len(subtitles) == 1
    assert subtitles[0].language == zht


def test_hant_alias_is_not_advertised_without_matching_results():
    # SubDL returns ZH_BG as zho-TW. Advertising zho-Hant as a separate provider
    # language made the request succeed but filtered the returned zho-TW row.
    assert Language("zho", script="Hant") not in SubdlProvider.languages


def test_filename_selected_unpack_file_keeps_episode_match(requests_mock):
    video = Episode(
        "Show.S01E05.mkv",
        "Show",
        1,
        5,
        series_imdb_id="tt1234567",
    )
    item = {
        "url": "/subtitle/show-season-1.zip",
        "name": "show-season-1.zip",
        "language": "EN",
        "subtitlePage": "/s/info/season",
        "releases": ["Show.S01.Complete"],
        "author": "someone",
        "season": 1,
        "episode": 0,
        "full_season": True,
        "unpack_files": [
            {
                "url": "/subtitle/show-s01e05.srt",
                "file_n_id": "file5",
                "name": "05 Episode Five.en.srt",
                "season": 1,
                "episode": 0,
                "hi": False,
            }
        ],
    }
    requests_mock.get(
        SEARCH_URL,
        json={"status": True, "subtitles": [item], "totalPages": 1},
    )

    with SubdlProvider("fake-key") as provider:
        subtitles = provider.list_subtitles(video, {Language("eng")})

    assert len(subtitles) == 1
    assert subtitles[0].is_direct_file is True
    assert subtitles[0].episode == 5
    assert "episode" in subtitles[0].matches


def test_unpack_selection_uses_effective_hi_class(requests_mock):
    video = Episode(
        "Show.S01E05.mkv",
        "Show",
        1,
        5,
        series_imdb_id="tt1234567",
    )
    item = {
        "url": "/subtitle/show-season-1.zip",
        "name": "show-season-1.zip",
        "language": "EN",
        "subtitlePage": "/s/info/season-hi",
        "releases": ["Show.S01.Complete"],
        "comment": "SDH version",
        "author": "someone",
        "season": 1,
        "episode": 0,
        "hi": False,
        "full_season": True,
        "unpack_files": [
            {
                "url": "/subtitle/show-s01e05.srt",
                "file_n_id": "normal5",
                "name": "Show.S01E05.srt",
                "season": 1,
                "episode": 5,
                "hi": False,
            },
            {
                "url": "/subtitle/show-s01e05-sdh.srt",
                "file_n_id": "sdh5",
                "name": "Show.S01E05.SDH.srt",
                "season": 1,
                "episode": 5,
                "hi": True,
            },
        ],
    }
    requests_mock.get(
        SEARCH_URL,
        json={"status": True, "subtitles": [item], "totalPages": 1},
    )

    with SubdlProvider("fake-key") as provider:
        subtitles = provider.list_subtitles(
            video,
            {Language.rebuild(Language("eng"), hi=True)},
        )

    assert len(subtitles) == 1
    assert subtitles[0].download_link == "/subtitle/show-s01e05-sdh.srt"
    assert subtitles[0].hearing_impaired is True


def test_search_404_is_service_unavailable(movies, requests_mock):
    requests_mock.get(SEARCH_URL, status_code=404, text="Not found")

    with SubdlProvider("fake-key") as provider:
        with pytest.raises(
            ServiceUnavailable, match="search endpoint unavailable"
        ):
            provider.list_subtitles(movies["dune"], {Language("eng")})


def test_remote_policy_limits_pages_and_disables_fallbacks(episodes, requests_mock):
    requests_mock.get(
        SEARCH_URL,
        json={
            "status": True,
            "subtitles": [],
            "totalPages": 4,
            "bazarr_policy": {
                "revision": 2,
                "enabled": True,
                "ai_translation_enabled": True,
                "max_pages": 1,
                "season_fallback_enabled": False,
                "title_fallback_enabled": False,
                "unpack_enabled": False,
                "message": None,
            },
        },
    )

    with SubdlProvider("fake-key") as provider:
        assert provider.list_subtitles(
            episodes["got_s03e10"], {Language("eng")}
        ) == []

    assert len(requests_mock.request_history) == 1


def test_remote_policy_disables_provider(movies, requests_mock):
    requests_mock.get(
        SEARCH_URL,
        json={
            "status": False,
            "error": "provider_disabled",
            "bazarr_policy": {
                "revision": 3,
                "enabled": False,
                "ai_translation_enabled": False,
                "max_pages": 1,
                "season_fallback_enabled": False,
                "title_fallback_enabled": False,
                "unpack_enabled": False,
                "message": "Maintenance",
            },
        },
    )

    with SubdlProvider("fake-key") as provider:
        assert provider.list_subtitles(movies["dune"], {Language("eng")}) == []

    assert len(requests_mock.request_history) == 1


def test_remote_policy_disables_ai_candidates(movies, requests_mock):
    body = search_response(entitled_translation())
    body["bazarr_policy"] = {
        "revision": 4,
        "enabled": True,
        "ai_translation_enabled": False,
        "max_pages": 2,
        "season_fallback_enabled": True,
        "title_fallback_enabled": True,
        "unpack_enabled": True,
        "message": None,
    }
    requests_mock.get(SEARCH_URL, json=body)

    with SubdlProvider("fake-key", ai_translate=True) as provider:
        assert provider.list_subtitles(movies["dune"], {Language("fas")}) == []
