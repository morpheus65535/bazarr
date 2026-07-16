import os

import pytest
from subliminal_patch.providers.subdl import SubdlProvider
from subliminal_patch.providers.subdl import SubdlSubtitle
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
