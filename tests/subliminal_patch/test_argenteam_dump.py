import pytest
from subliminal_patch.providers.argenteamdump import ArgenteamDumpProvider
from subzero.language import Language


def test_list_subtitles_movies(movies):
    languages = {Language("spa", "MX")}
    with ArgenteamDumpProvider() as provider:
        subtitles = provider.list_subtitles(movies["man_of_steel"], languages)
        assert subtitles

        provider.download_subtitle(subtitles[0])
        assert subtitles[0].is_valid()

def test_list_subtitles_episodes(episodes):
    languages = {Language("spa", "MX")}
    with ArgenteamDumpProvider() as provider:
        subtitles = provider.list_subtitles(episodes["got_s03e10"], languages)
        assert subtitles

        provider.download_subtitle(subtitles[0])
        assert subtitles[0].is_valid()
