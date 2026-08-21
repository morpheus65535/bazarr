# coding=utf-8

from unittest import mock

import pytest

from subzero.language import Language
from subliminal_patch.exceptions import MustGetBlacklisted

from app.get_providers import _handle_mgb


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_PROVIDER = 'someprovider'
_SUBS_ID = 'subtitle-1234'


def _ids(series_id=42, episode_id=99, radarr_id=7):
    # Built the way core.py does it: every key always present, None when the
    # video object had no such attribute.
    return {
        'radarrId': radarr_id,
        'sonarrSeriesId': series_id,
        'sonarrEpisodeId': episode_id,
    }


def _call(media_type, ids, language=None):
    exception = MustGetBlacklisted(_SUBS_ID, media_type)
    language = language or Language('eng')
    with mock.patch('app.get_providers.blacklist_log') as log, \
         mock.patch('app.get_providers.blacklist_log_movie') as log_movie:
        _handle_mgb(_PROVIDER, exception, ids, language)
    return log, log_movie


# ──────────────────────────────────────────────────────────────────────────────
# Series blacklisting – the guard used to test a misspelled key
# ──────────────────────────────────────────────────────────────────────────────
#
# _handle_mgb is how a provider says "this subtitle is broken, never offer it
# again" (MustGetBlacklisted). The series guard checked 'sonarrEpsiodeId', which
# is never a key in the ids dict, so blacklist_log was never called and the bad
# subtitle was re-selected on every subsequent search. Movies were unaffected.

def test_series_is_blacklisted():
    log, _ = _call('series', _ids())
    log.assert_called_once_with(42, 99, _PROVIDER, _SUBS_ID, 'en')


def test_movie_is_blacklisted():
    _, log_movie = _call('movie', _ids())
    log_movie.assert_called_once_with(7, _PROVIDER, _SUBS_ID, 'en')


def test_series_does_not_touch_the_movie_blacklist():
    log, log_movie = _call('series', _ids())
    assert log.called
    assert not log_movie.called


# ──────────────────────────────────────────────────────────────────────────────
# The ids must be known before a row is written
# ──────────────────────────────────────────────────────────────────────────────
#
# sonarr_series_id and sonarr_episode_id are ForeignKey columns on
# TableBlacklist, and the ids dict carries None rather than omitting a key. So
# the guard has to test the values: a key-presence check would always pass and
# write NULL foreign keys.

@pytest.mark.parametrize('series_id,episode_id', [
    (42, None),
    (None, 99),
    (None, None),
])
def test_series_without_known_ids_is_not_blacklisted(series_id, episode_id):
    log, _ = _call('series', _ids(series_id=series_id, episode_id=episode_id))
    assert not log.called


def test_no_ids_at_all_is_not_blacklisted():
    log, log_movie = _call('series', None)
    assert not log.called
    assert not log_movie.called


# ──────────────────────────────────────────────────────────────────────────────
# The language string recorded against the blacklist entry
# ──────────────────────────────────────────────────────────────────────────────

def test_plain_language_is_recorded_bare():
    log, _ = _call('series', _ids(), Language('eng'))
    assert log.call_args[0][4] == 'en'


def test_forced_language_is_suffixed():
    forced = Language.rebuild(Language('eng'), forced=True)
    log, _ = _call('series', _ids(), forced)
    assert log.call_args[0][4] == 'en:forced'


def test_hi_language_is_suffixed():
    hi = Language.rebuild(Language('eng'), hi=True)
    log, _ = _call('series', _ids(), hi)
    assert log.call_args[0][4] == 'en:hi'
