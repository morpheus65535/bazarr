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
        },
    )


def test_subtitle(subtitle):
    assert subtitle.language == Language.fromietf("fr")
    assert subtitle.id == "d28b4d5b-7dcc-47b3-8232-fb02f081d135"
    assert subtitle.hearing_impaired == False


def test_subtitle_get_matches(subtitle, episodes):
    matches = subtitle.get_matches(episodes["better_call_saul_s06e04"])

    assert matches.issuperset(("series", "title", "season", "episode", "source"))
    assert "resolution" not in matches


def test_subtitle_download(subtitle):
    with GestdownProvider() as provider:
        provider.download_subtitle(subtitle)
        assert subtitle.content is not None
        assert subtitle.is_valid()


def test_list_subtitles_423(episodes, requests_mock, mocker):
    mocker.patch("time.sleep")
    requests_mock.get(
        f"{_BASE_URL}/subtitles/find/English/Breaking%20Bad/1/1", status_code=423
    )

    with GestdownProvider() as provider:
        assert not provider.list_subtitles(
            episodes["breaking_bad_s01e01"], {Language.fromietf("en")}
        )
