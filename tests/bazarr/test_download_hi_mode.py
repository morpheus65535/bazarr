# coding=utf-8

from unittest import mock

import pytest

from subzero.language import Language


def _item(language, hi, forced="False"):
    return {'language': language, 'hi': hi, 'forced': forced}


def _hi_modes_searched(items, languages):
    """Run generate_subtitles and return {language: hearing_impaired mode} given to the provider search."""
    video = mock.MagicMock()
    video.original_path = '/media/tv/Show/S01E01.mkv'

    settings = mock.MagicMock()
    settings.general.utf8_encode = False
    settings.embeddedsubtitles.prefer_embedded = False

    modes = {}

    def fake_download(videos, languages, hearing_impaired, **kwargs):
        modes[next(iter(languages))] = hearing_impaired
        return {}

    with mock.patch('subtitles.download.settings', settings), \
         mock.patch('subtitles.download.get_profiles_list',
                    return_value={'originalFormat': False, 'items': items}), \
         mock.patch('subtitles.download._get_pool') as pool, \
         mock.patch('subtitles.download._get_language_obj', return_value=languages), \
         mock.patch('subtitles.download._set_forced_providers'), \
         mock.patch('subtitles.download._get_scores', return_value=(0, 100, {})), \
         mock.patch('subtitles.download.get_video', return_value=video), \
         mock.patch('subtitles.download.download_best_subtitles', side_effect=fake_download), \
         mock.patch('subtitles.download.subliminal'):
        pool.return_value.providers = ['someprovider']
        from subtitles.download import generate_subtitles
        list(generate_subtitles('/media/tv/Show/S01E01.mkv', [('en', 'False', 'False')], 'English', None, 'Show', 'series', 1))
    return modes


NORMAL = Language('eng')
HI = Language.rebuild(Language('eng'), hi=True)


@pytest.mark.parametrize('items', [
    [_item('en', 'False'), _item('en', 'True')],
    [_item('en', 'True'), _item('en', 'False')],
])
def test_same_language_normal_and_hi_keep_their_own_mode(items):
    modes = _hi_modes_searched(items, [NORMAL, HI])
    assert modes[HI] == 'force HI'
    assert modes[NORMAL] == "don't prefer"


def test_excluded_item_still_forces_non_hi_for_normal_language():
    modes = _hi_modes_searched([_item('en', 'Excluded')], [NORMAL])
    assert modes[NORMAL] == 'force non-HI'


def test_excluded_normal_item_next_to_hi_item():
    modes = _hi_modes_searched([_item('en', 'Excluded'), _item('en', 'True')], [NORMAL, HI])
    assert modes[NORMAL] == 'force non-HI'
    assert modes[HI] == 'force HI'
