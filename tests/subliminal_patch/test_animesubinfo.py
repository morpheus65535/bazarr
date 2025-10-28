# -*- coding: utf-8 -*-
import pytest

from subliminal_patch.core import Episode
from subliminal_patch.providers.animesubinfo import AnimesubinfoProvider
from subzero.language import Language


@pytest.fixture
def demon_slayer_episode():
    """Fixture for Demon Slayer episode 1 with English title."""
    return Episode(
        name='Demon Slayer - S01E01.mkv',
        series='Demon Slayer',
        season=1,
        episode=1,
    )


@pytest.fixture
def kimetsu_no_yaiba_episode():
    """Fixture for Demon Slayer episode 1 with Japanese title."""
    return Episode(
        name='Kimetsu no Yaiba - S01E01.mkv',
        series='Kimetsu no Yaiba',
        season=1,
        episode=1,
    )


@pytest.mark.vcr
def test_list_subtitles_english_title(demon_slayer_episode):
    """Test listing subtitles for Demon Slayer with English title."""
    with AnimesubinfoProvider() as provider:
        subs = provider.list_subtitles(demon_slayer_episode, [Language('pol')])
        assert isinstance(subs, list)


@pytest.mark.vcr
def test_list_subtitles_japanese_title(kimetsu_no_yaiba_episode):
    """Test listing subtitles for Kimetsu no Yaiba with Japanese title."""
    with AnimesubinfoProvider() as provider:
        subs = provider.list_subtitles(kimetsu_no_yaiba_episode, [Language('pol')])

        # Assert exact values from cassette
        assert len(subs) == 4

        sub = subs[0]
        assert sub.language == Language('pol')
        assert sub.subtitle_id == '68055'
        assert sub.title_org == 'Kimetsu no Yaiba ep01'
        assert sub.title_eng == 'Demon Slayer ep01'
        assert sub.title_alt == 'Kimetsu no Yaiba ep01'
        assert sub.author == 'Askara'
        assert sub.format_type == 'Advanced SSA'
        assert sub.size == '11kB'
        assert sub.download_hash == '8e2c0dfbd6f4691f12bcf0088c6a021fdf98db33'
        assert sub.page_link == 'http://animesub.info/'
        assert sub.release_info == 'Kimetsu no Yaiba ep01 - Demon Slayer ep01'


@pytest.mark.vcr
def test_download_subtitle(kimetsu_no_yaiba_episode):
    """Test downloading a subtitle with exact content validation."""
    with AnimesubinfoProvider() as provider:
        subs = provider.list_subtitles(kimetsu_no_yaiba_episode, [Language('pol')])

        assert len(subs) == 4

        subtitle = subs[0]
        provider.download_subtitle(subtitle)

        # Assert exact content properties
        assert subtitle.content is not None
        assert len(subtitle.content) == 46866

        # Verify it's a valid subtitle format (Advanced SSA)
        content_str = subtitle.content.decode('utf-8', errors='ignore') if isinstance(subtitle.content, bytes) else subtitle.content
        print(content_str)
        assert '[Script Info]' in content_str
        assert 'Dialogue:' in content_str


@pytest.mark.vcr
def test_list_subtitles_polish_language(demon_slayer_episode):
    """Test that only Polish language is requested and returned."""
    with AnimesubinfoProvider() as provider:
        subs = provider.list_subtitles(demon_slayer_episode, [Language('pol')])

        # All subtitles should be Polish
        for sub in subs:
            assert sub.language == Language('pol')


@pytest.mark.vcr
def test_subtitle_attributes(kimetsu_no_yaiba_episode):
    """Test that subtitles have all required attributes with exact values."""
    with AnimesubinfoProvider() as provider:
        subs = provider.list_subtitles(kimetsu_no_yaiba_episode, [Language('pol')])

        assert len(subs) == 4

        sub = subs[0]
        # Assert exact attribute values from cassette
        assert sub.subtitle_id == '68055'
        assert sub.title_org == 'Kimetsu no Yaiba ep01'
        assert sub.title_eng == 'Demon Slayer ep01'
        assert sub.title_alt == 'Kimetsu no Yaiba ep01'
        assert sub.author == 'Askara'
        assert sub.format_type == 'Advanced SSA'
        assert sub.size == '11kB'
        assert sub.download_hash == '49efec8753338e4b2dee9545600c803129fb8bb2'
        assert sub.language == Language('pol')
        assert sub.page_link == 'http://animesub.info/'
        assert sub.release_info == 'Kimetsu no Yaiba ep01 - Demon Slayer ep01'


def test_provider_initialization():
    """Test that provider initializes correctly."""
    with AnimesubinfoProvider() as provider:
        assert provider.session is not None
        assert provider.languages == {Language('pol')}
        assert Episode in provider.video_types


def test_provider_languages():
    """Test that provider only supports Polish."""
    provider = AnimesubinfoProvider()
    assert Language('pol') in provider.languages
    assert len(provider.languages) == 1
