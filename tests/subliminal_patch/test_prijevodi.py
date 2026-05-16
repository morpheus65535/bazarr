import os
import zipfile

import pytest
import subliminal
from subzero.language import Language
from subliminal_patch.providers.prijevodionline import PrijevodiOnlineProvider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending
from subliminal_patch.core import Episode

BASE_URL = 'https://www.prijevodi-online.org'

# S01E06 "A Golden Crown" – epizoda id 34272
#   HR subtitles: 21705, 21868, 22612, 35306, 120303  (5 total)
#   SR subtitles: 21710, 21728, 21748, 21757, 22259, 37142  (6 total)
#   All statuses "provjereno" in the fixture HTML.
#   Subtitle 37142 is the SR REWARD/720pBluRay release (opis: 720p.BluRay.X264-REWARD).


@pytest.fixture(scope="session")
def region():
    subliminal.region.configure('dogpile.cache.memory', replace_existing_backend=True)


@pytest.fixture(scope="session")
def got_s01e06():
    return Episode(
        "Game.of.Thrones.S01E06.720p.BluRay.X264-REWARD.mkv",
        "Game of Thrones",
        1,
        6,
        release_group="REWARD",
        resolution="720p",
        video_codec="H.264",
    )


def _mock_list_subtitles(requests_mock, data):
    """Register the three HTTP mocks needed by list_subtitles for GOT S01E06."""
    with open(os.path.join(data, 'prijevodi_index_g.html'), 'rb') as f:
        requests_mock.get(f'{BASE_URL}/serije/index/g', content=f.read())
    with open(os.path.join(data, 'prijevodi_got.html'), 'rb') as f:
        requests_mock.get(f'{BASE_URL}/serije/view/935/game-of-thrones', content=f.read())
    with open(os.path.join(data, 'prijevodi_ep34272.html'), 'rb') as f:
        requests_mock.post(f'{BASE_URL}/prijevod/get/34272', content=f.read())


def test_list_subtitles_hr(region, got_s01e06, requests_mock, data):
    _mock_list_subtitles(requests_mock, data)

    with PrijevodiOnlineProvider() as provider:
        subtitles = provider.list_subtitles(got_s01e06, {Language('hrv')})

    assert len(subtitles) == 5
    assert all(s.language == Language('hrv') for s in subtitles)
    assert all(s.series == 'Game of Thrones' for s in subtitles)
    assert all(s.season == 1 for s in subtitles)
    assert all(s.episode == 6 for s in subtitles)
    assert all(s.verified for s in subtitles)
    # verified subtitles sort first (all are verified here, so just check order is stable)
    assert subtitles[0].verified


def test_list_subtitles_sr(region, got_s01e06, requests_mock, data):
    _mock_list_subtitles(requests_mock, data)

    with PrijevodiOnlineProvider() as provider:
        subtitles = provider.list_subtitles(got_s01e06, {Language('srp')})

    assert len(subtitles) == 4
    assert all(s.language == Language('srp') for s in subtitles)
    assert all(s.season == 1 for s in subtitles)
    assert all(s.episode == 6 for s in subtitles)
    assert all(s.verified for s in subtitles)


def test_list_subtitles_series_not_found(region, requests_mock, data):
    with open(os.path.join(data, 'prijevodi_index_g.html'), 'rb') as f:
        requests_mock.get(f'{BASE_URL}/serije/index/g', content=f.read())

    video = Episode(
        "Galaxy.Nonsense.Show.S01E01.mkv",
        "Galaxy Nonsense Show",
        1,
        1,
    )
    with PrijevodiOnlineProvider() as provider:
        subtitles = provider.list_subtitles(video, {Language('hrv')})

    assert subtitles == []


def test_get_matches_reward_release(region, got_s01e06, requests_mock, data):
    """Subtitle 37142 (SR, REWARD 720p BluRay) should match series+season+episode+release_group."""
    _mock_list_subtitles(requests_mock, data)

    with PrijevodiOnlineProvider() as provider:
        subtitles = provider.list_subtitles(got_s01e06, {Language('srp')})

    reward = next((s for s in subtitles if s.subtitle_id == 37142), None)
    assert reward is not None
    assert reward.release_info == '720p.BluRay.X264-REWARD / Preveo dragan4e'

    matches = reward.get_matches(got_s01e06)
    assert 'series' in matches
    assert 'season' in matches
    assert 'episode' in matches
    assert 'release_group' in matches


def test_download_subtitle_zip(region, got_s01e06, requests_mock, data):
    """Download subtitle 37142 (SR, REWARD), extract from zip, verify content."""
    _mock_list_subtitles(requests_mock, data)

    sub_url = (
        f'{BASE_URL}/preuzmi-prijevod/epizoda/37142'
        f'/game-of-thrones-01x06-a-golden-crown-720pbluray-sr'
    )
    with open(os.path.join(data, 'prijevodi_sub_37143.zip'), 'rb') as f:
        requests_mock.get(sub_url, content=f.read())

    with PrijevodiOnlineProvider() as provider:
        subtitles = provider.list_subtitles(got_s01e06, {Language('srp')})
        reward = next(s for s in subtitles if s.subtitle_id == 37142)
        provider.download_subtitle(reward)

    assert reward.content is not None

    # Verify content matches the first subtitle file extracted from the archive
    with zipfile.ZipFile(os.path.join(data, 'prijevodi_sub_37143.zip')) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(SUBTITLE_EXTENSIONS)]
        expected = fix_line_ending(zf.read(names[0]))

    assert reward.content == expected
