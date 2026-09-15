# coding=utf-8

import logging
import os
from unittest import mock

import pytest

from subzero.language import Language

from subtitles.download import _blacklist_unusable_subtitles


# ──────────────────────────────────────────────────────────────────────────────
# Helper functions/classes
# ──────────────────────────────────────────────────────────────────────────────
_PROVIDER = 'someprovider'
_SUBS_ID = 'subtitle-1234'


class _Video:
    def __init__(self, **ids):
        for name, value in ids.items():
            setattr(self, name, value)


class _Subtitle:
    def __init__(self, provider_name=_PROVIDER, subs_id=_SUBS_ID):
        self.provider_name = provider_name
        self.id = subs_id
        self.format = 'srt'
        self.mods = None


def _episode_video():
    return _Video(sonarrSeriesId=42, sonarrEpisodeId=99)

def _movie_video():
    return _Video(radarrId=7)

def _no_id_video():
    return _Video()

def _blacklist(video, media_type, subtitles=None, language=None):
    subtitles = [_Subtitle()] if subtitles is None else subtitles
    language = language or Language('eng')
    with mock.patch('app.get_providers.blacklist_log') as log, \
         mock.patch('app.get_providers.blacklist_log_movie') as log_movie:
        _blacklist_unusable_subtitles(video, subtitles, media_type, language)
    return log, log_movie


# ──────────────────────────────────────────────────────────────────────────────
# An undecodable subtitle is recorded so it is not downloaded again
# ──────────────────────────────────────────────────────────────────────────────
def test_episode_subtitle_is_blacklisted():
    log, _ = _blacklist(_episode_video(), 'series')
    log.assert_called_once_with(42, 99, _PROVIDER, _SUBS_ID, 'en')


def test_movie_subtitle_is_blacklisted():
    _, log_movie = _blacklist(_movie_video(), 'movie')
    log_movie.assert_called_once_with(7, _PROVIDER, _SUBS_ID, 'en')


def test_forced_language_is_recorded():
    forced = Language.rebuild(Language('eng'), forced=True)
    log, _ = _blacklist(_episode_video(), 'series', language=forced)
    assert log.call_args[0][4] == 'en:forced'


def test_every_subtitle_in_the_batch_is_blacklisted():
    subtitles = [_Subtitle(subs_id='a'), _Subtitle(subs_id='b')]
    log, _ = _blacklist(_episode_video(), 'series', subtitles=subtitles)
    assert [call[0][3] for call in log.call_args_list] == ['a', 'b']


# ──────────────────────────────────────────────────────────────────────────────
# A video with no known ids writes nothing - don't blacklist nulls!
# ──────────────────────────────────────────────────────────────────────────────
def test_no_id_video_is_not_blacklisted():
    log, log_movie = _blacklist(_no_id_video(), 'series')
    assert not log.called
    assert not log_movie.called


def test_no_id_video_is_logged(caplog):
    with caplog.at_level(logging.DEBUG):
        _blacklist(_Video(), 'movie')
    assert 'cannot blacklist' in caplog.text


# ──────────────────────────────────────────────────────────────────────────────
# Only UnicodeError should blacklist files
# ──────────────────────────────────────────────────────────────────────────────
def _run_generate_subtitles(save_error):
    video = _episode_video()
    video.original_path = '/media/tv/Show/S01E01.mkv'
    subtitle = _Subtitle()

    settings = mock.MagicMock()
    settings.general.utf8_encode = False
    settings.general.chmod_enabled = False
    settings.general.single_language = False

    with mock.patch('subtitles.download.settings', settings), \
         mock.patch('subtitles.download.get_array_from', return_value=[]), \
         mock.patch('subtitles.download.get_profiles_list',
                    return_value={'originalFormat': False, 'items': []}), \
         mock.patch('subtitles.download._get_pool') as pool, \
         mock.patch('subtitles.download._get_language_obj', return_value=[Language('eng')]), \
         mock.patch('subtitles.download._set_forced_providers'), \
         mock.patch('subtitles.download._get_scores', return_value=(0, 100, {})), \
         mock.patch('subtitles.download.get_video', return_value=video), \
         mock.patch('subtitles.download.get_target_folder', return_value='/media/tv/Show'), \
         mock.patch('subtitles.download.download_best_subtitles',
                    return_value={video: [subtitle]}), \
         mock.patch('subtitles.download.save_subtitles', side_effect=save_error), \
         mock.patch('app.get_providers.blacklist_log') as log, \
         mock.patch('app.get_providers.blacklist_log_movie') as log_movie:
        pool.return_value.providers = ['someprovider']
        from subtitles.download import generate_subtitles
        list(generate_subtitles('/media/tv/Show/S01E01.mkv', ['en'], 'English', None,
                                'Show', 'series', 1))
    return log, log_movie


@pytest.mark.parametrize('error', [
    UnicodeDecodeError('utf-8', b'x', 0, 1, 'invalid start byte'),
    UnicodeEncodeError('ascii', 'x', 0, 1, 'ordinal not in range'),
])
def test_undecodable_subtitle_is_blacklisted(error):
    # Both directions matter: get_modified_content decodes and re-encodes.
    log, _ = _run_generate_subtitles(error)
    log.assert_called_once_with(42, 99, _PROVIDER, _SUBS_ID, 'en')


@pytest.mark.parametrize('error', [
    OSError(28, 'No space left on device'),
    PermissionError(13, 'Permission denied'),
    FileNotFoundError(2, 'No such file or directory'),
])
def test_environmental_failure_is_not_blacklisted(error):
    log, log_movie = _run_generate_subtitles(error)
    assert not log.called
    assert not log_movie.called


# ──────────────────────────────────────────────────────────────────────────────
# Only the subtitle that actually failed gets blacklisted
# ──────────────────────────────────────────────────────────────────────────────
#
# save_subtitles aborts mid-loop, so the caller only has the list it passed in
# and cannot tell which member failed. It therefore tags the exception with that
# subtitle. Without the tag the whole batch would be blacklisted, banning good
# subtitles alongside the bad one.

def _blacklist_with_tag(failed_subtitle, subtitles):
    with mock.patch('app.get_providers.blacklist_log') as log, \
         mock.patch('app.get_providers.blacklist_log_movie'):
        _blacklist_unusable_subtitles(_episode_video(), subtitles, 'series',
                                      Language('eng'), failed_subtitle)
    return [call[0][3] for call in log.call_args_list]


def test_only_the_tagged_subtitle_is_blacklisted():
    good_a, bad, good_b = _Subtitle(subs_id='a'), _Subtitle(subs_id='bad'), _Subtitle(subs_id='b')
    assert _blacklist_with_tag(bad, [good_a, bad, good_b]) == ['bad']


def test_untagged_falls_back_to_the_whole_batch():
    # Nothing should reach this today, but blacklisting nothing would let the
    # download loop resume, which is what the feature exists to stop.
    subtitles = [_Subtitle(subs_id='a'), _Subtitle(subs_id='b')]
    assert _blacklist_with_tag(None, subtitles) == ['a', 'b']


def test_save_subtitles_tags_the_failing_subtitle():
    # The other half of the contract, against the real save_subtitles.
    import tempfile
    from subliminal_patch.core import save_subtitles

    class _Savable:
        def __init__(self, subs_id, language, decodable):
            self.id = subs_id
            self.provider_name = _PROVIDER
            self.content = b'1\n00:00:01,000 --> 00:00:02,000\nhi\n\n'
            self.text = '1\n00:00:01,000 --> 00:00:02,000\nhi\n\n'
            self.language = language
            self.format = 'srt'
            self.mods = None
            self.storage_path = None
            self._decodable = decodable

        def get_modified_content(self, format='srt', debug=False):
            if not self._decodable:
                raise UnicodeDecodeError('utf-8', b'\xbf', 0, 1, 'invalid start byte')
            return self.content

    good = _Savable('good', Language('eng'), True)
    bad = _Savable('bad', Language('fra'), False)

    with tempfile.TemporaryDirectory() as directory:
        with pytest.raises(UnicodeDecodeError) as raised:
            save_subtitles(os.path.join(directory, 'video.mkv'), [good, bad], directory=directory)

    assert raised.value.bazarr_failed_subtitle is bad
