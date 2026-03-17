import pytest
from subliminal_patch.language import PatchedAddic7edConverter
from subliminal_patch.providers.gestdown import _BASE_URL
from subliminal_patch.providers.gestdown import GestdownProvider
from subliminal_patch.providers.gestdown import GestdownSubtitle
from subzero.language import Language


def test_language_list_is_convertible():
    converter = PatchedAddic7edConverter()
    for language in GestdownProvider.languages:
        converter.convert(language.alpha3)


@pytest.mark.parametrize(
    "episode_key,language,expected_any_release_info",
    [
        ("breaking_bad_s01e01", Language.fromietf("en"), "BluRayREWARD"),
        ("better_call_saul_s06e04", Language.fromietf("fr"), "AMZN-NTb"),
    ],
)
def test_list_subtitles(episodes, episode_key, language, expected_any_release_info):
    with GestdownProvider() as provider:
        subtitles = provider.list_subtitles(episodes[episode_key], {language})
        assert any(
            subtitle.release_info == expected_any_release_info for subtitle in subtitles
        )


def test_list_subtitles_hearing_impaired(episodes):
    with GestdownProvider() as provider:
        subtitles = provider.list_subtitles(
            episodes["better_call_saul_s06e04"], {Language.fromietf("en")}
        )
        assert not all(subtitle.hearing_impaired for subtitle in subtitles)
        assert any(subtitle.hearing_impaired for subtitle in subtitles)


def test_list_subtitles_inexistent(episodes):
    with GestdownProvider() as provider:
        assert not provider.list_subtitles(
            episodes["inexistent"], {Language.fromietf("en")}
        )


@pytest.fixture
def subtitle():
    return GestdownSubtitle(
        Language.fromietf("fr"),
        {
            "subtitleId": "d28b4d5b-7dcc-47b3-8232-fb02f081d135",
            "version": "480p.AMZN.WEB-DL.NTb",
            "hearingImpaired": False,
            "downloadUri": "/subtitles/download/d28b4d5b-7dcc-47b3-8232-fb02f081d135",
            "qualities": [],
        },
    )


def test_subtitle(subtitle):
    assert subtitle.language == Language.fromietf("fr")
    assert subtitle.id == "d28b4d5b-7dcc-47b3-8232-fb02f081d135"
    assert subtitle.hearing_impaired == False
    assert subtitle.releases == ["480p.AMZN.WEB-DL.NTb"]
    assert subtitle.qualities == []


def test_subtitle_get_matches(subtitle, episodes):
    matches = subtitle.get_matches(episodes["better_call_saul_s06e04"])

    assert matches.issuperset(("series", "title", "season", "episode", "source"))
    assert "resolution" not in matches


def test_subtitle_multi_release_version():
    sub = GestdownSubtitle(
        Language.fromietf("en"),
        {
            "subtitleId": "abc",
            "version": "HDTV, WEB",
            "hearingImpaired": False,
            "downloadUri": "/download/abc",
            "qualities": [],
        },
    )
    assert sub.releases == ["HDTV", "WEB"]
    assert sub.release_info == "HDTV\nWEB"


def test_subtitle_get_matches_release_group(episodes):
    sub = GestdownSubtitle(
        Language.fromietf("en"),
        {
            "subtitleId": "abc",
            "version": "BluRay.720p.REWARD",
            "hearingImpaired": False,
            "downloadUri": "/download/abc",
            "qualities": [],
            "qualities": [],
        },
    )
    matches = sub.get_matches(episodes["breaking_bad_s01e01"])
    assert "release_group" in matches


def test_subtitle_get_matches_resolution_from_qualities(episodes):
    sub = GestdownSubtitle(
        Language.fromietf("en"),
        {
            "subtitleId": "abc",
            "version": "HDTV",
            "hearingImpaired": False,
            "downloadUri": "/download/abc",
            "qualities": ["720p", "1080p"],
        },
    )
    matches = sub.get_matches(episodes["breaking_bad_s01e01"])
    assert "resolution" in matches


def test_subtitle_download(subtitle):
    with GestdownProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.content is not None
        assert subtitle.is_valid()


def test_list_subtitles_423(episodes, requests_mock, mocker):
    mocker.patch("time.sleep")
    requests_mock.get(
        "https://api.gestdown.info/shows/external/tvdb/81189",
        status_code=200,
        text='{"shows":[{"id":"cd880e2e-ef44-47cd-9f3d-a03b343ba2d0","name":"Breaking Bad","nbSeasons":5,"seasons":[1,2,3,4,5]}]}',
    )
    requests_mock.get(
        f"{_BASE_URL}/subtitles/get/cd880e2e-ef44-47cd-9f3d-a03b343ba2d0/1/1/English",
        status_code=423,
    )

    with GestdownProvider() as provider:
        assert not provider.list_subtitles(
            episodes["breaking_bad_s01e01"], {Language.fromietf("en")}
        )
