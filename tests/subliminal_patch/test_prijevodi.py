import json
import os
import zipfile

import pytest
import requests
import subliminal
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending
from subliminal.score import compute_score
from subliminal_patch.core import Episode, Movie
from subliminal_patch.exceptions import ForbiddenError, IPAddressBlocked, TooManyRequests
import subliminal_patch.providers.prijevodionline as prijevodionline_module
from subliminal_patch.providers.prijevodionline import PrijevodiOnlineProvider
from subzero.language import Language

API_URL = 'https://www.prijevodi-online.org/api/v1'
API_KEY = 'po_testkey'

# Dexter S01E01 (series id 116, episode id 6359). Translations on the site:
#   137886 hr, 39041 mk (ignored), 20749 bs, 20748 bs, 20747 sr
TRANSLATION_HR = 137886
TRANSLATION_SR = 20747


@pytest.fixture(scope="session")
def region():
    subliminal.region.configure('dogpile.cache.memory', replace_existing_backend=True)


@pytest.fixture(scope="session")
def dexter_s01e01():
    return Episode(
        "Dexter.S01E01.720p.BluRay.x264-DEMAND.mkv",
        "Dexter",
        1,
        1,
        release_group="DEMAND",
        resolution="720p",
        video_codec="H.264",
    )


def _load(data, name):
    with open(os.path.join(data, name), 'rb') as f:
        return f.read()


def _translations(data, changes):
    """Load the recorded translations, changing the flags of the given translation ids.

    :param dict changes: Mapping of translation id to the fields to override on that item.
    """
    payload = json.loads(_load(data, 'prijevodi_translations_dexter_s01e01.json'))
    for item in payload['translations']['items']:
        item.update(changes.get(item['id'], {}))
    return payload


def _mock_lookup(requests_mock, data, translations=None):
    """Register the series, episode and translation routes for Dexter S01E01."""
    requests_mock.get(f'{API_URL}/series?search=Dexter',
                      content=_load(data, 'prijevodi_series_search_dexter.json'))
    requests_mock.get(f'{API_URL}/series/116/episodes', content=_load(data, 'prijevodi_episodes_dexter_s01.json'))
    requests_mock.get(f'{API_URL}/translations/series?episodeId=6359', json=translations or json.loads(
        _load(data, 'prijevodi_translations_dexter_s01e01.json')))


def _ticket_response(**download):
    return {'download': {'outcome': 'ticket', 'ticket': 'abc', **download}}


def _refused(refusal):
    return {'download': {'outcome': 'refused', 'refusal': refusal}}


# Configuration and authentication

def test_requests_identify_as_bazarr(region, dexter_s01e01, requests_mock, data, monkeypatch):
    monkeypatch.setenv('SZ_USER_AGENT', 'Bazarr/1.2.3')
    _mock_lookup(requests_mock, data)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert all(r.headers['User-Agent'] == 'Bazarr/1.2.3' for r in requests_mock.request_history)


def test_user_agent_falls_back_to_bazarr(region, requests_mock, monkeypatch):
    monkeypatch.delenv('SZ_USER_AGENT', raising=False)
    requests_mock.get(f'{API_URL}/series?search=Dexter', json={'series': {'items': [], 'total': 0}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        provider.list_subtitles(
            Episode("Dexter.S01E01.mkv", "Dexter", 1, 1), {Language('hrv')})

    assert requests_mock.request_history[0].headers['User-Agent'] == 'Bazarr'


def test_missing_api_key_raises_without_any_request(region, dexter_s01e01, requests_mock):
    with pytest.raises(ConfigurationError):
        PrijevodiOnlineProvider(api_key='')
    with pytest.raises(ConfigurationError):
        PrijevodiOnlineProvider()

    assert requests_mock.call_count == 0


def test_malformed_api_key_raises_without_any_request(region, requests_mock):
    with pytest.raises(ConfigurationError, match='po_'):
        PrijevodiOnlineProvider(api_key='not-a-key')

    assert requests_mock.call_count == 0


def test_invalid_api_key_raises_authentication_error(region, dexter_s01e01, requests_mock):
    requests_mock.get(f'{API_URL}/series?search=Dexter', status_code=401, json={
        'error': {'code': 'API_KEY_INVALID', 'message': 'Invalid API key', 'requestId': 'x'}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        with pytest.raises(AuthenticationError, match='API_KEY_INVALID'):
            provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert requests_mock.request_history[0].headers['Authorization'] == f'Bearer {API_KEY}'


def test_inactive_subscription_raises_authentication_error(region, dexter_s01e01, requests_mock):
    requests_mock.get(f'{API_URL}/series?search=Dexter', status_code=401, json={
        'error': {'code': 'API_KEY_SUBSCRIPTION_INACTIVE', 'message': 'API pristup inactive', 'requestId': 'x'}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        with pytest.raises(AuthenticationError, match='API_KEY_SUBSCRIPTION_INACTIVE'):
            provider.list_subtitles(dexter_s01e01, {Language('hrv')})


def test_missing_read_grant_raises_forbidden_error(region, dexter_s01e01, requests_mock):
    requests_mock.get(f'{API_URL}/series?search=Dexter', status_code=403, json={
        'error': {'code': 'Auth/Forbidden', 'message': 'Missing permission: series.read'}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        with pytest.raises(ForbiddenError, match='series.read'):
            provider.list_subtitles(dexter_s01e01, {Language('hrv')})


def test_missing_movie_grant_raises_forbidden_error(region, requests_mock):
    requests_mock.get(f'{API_URL}/movies?search=Inception', status_code=403, json={
        'error': {'code': 'Auth/Forbidden', 'message': 'Missing permission: movies.read'}})

    with PrijevodiOnlineProvider(api_key=API_KEY, allow_paid_translations=True) as provider:
        with pytest.raises(ForbiddenError, match='movies.read'):
            provider.list_subtitles(Movie("Inception.2010.mkv", "Inception", 2010), {Language('hrv')})


def test_missing_download_grant_raises_forbidden_error(region, dexter_s01e01, requests_mock, data):
    _mock_lookup(requests_mock, data)
    requests_mock.post(f'{API_URL}/downloads/ticket', status_code=403, json={
        'error': {'code': 'Auth/Forbidden', 'message': 'Missing permission: series.translations.download'}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})
        assert [s.subtitle_id for s in subtitles] == [TRANSLATION_HR]
        with pytest.raises(ForbiddenError, match='series.translations.download'):
            provider.download_subtitle(subtitles[0])


def test_rate_limit_raises_too_many_requests(region, dexter_s01e01, requests_mock):
    requests_mock.get(f'{API_URL}/series?search=Dexter', status_code=429,
                      headers={'Retry-After': '30'}, json={'error': {'code': 'RateLimit/Exceeded'}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        with pytest.raises(TooManyRequests, match='Retry-After 30'):
            provider.list_subtitles(dexter_s01e01, {Language('hrv')})


# Listing

def test_list_subtitles_hr(region, dexter_s01e01, requests_mock, data):
    _mock_lookup(requests_mock, data)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert [s.subtitle_id for s in subtitles] == [TRANSLATION_HR]
    assert subtitles[0].language == Language('hrv')
    assert subtitles[0].titles[0] == 'Dexter'
    assert subtitles[0].season == 1
    assert subtitles[0].episode == 1
    assert subtitles[0].paid is False


def test_list_subtitles_srp(region, dexter_s01e01, requests_mock, data):
    _mock_lookup(requests_mock, data)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('srp')})

    assert [s.subtitle_id for s in subtitles] == [TRANSLATION_SR]


def test_list_subtitles_hbs_merges_languages(region, dexter_s01e01, requests_mock, data):
    _mock_lookup(requests_mock, data)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hbs')})

    # The Macedonian translation is not a requested language and is skipped.
    assert sorted(s.subtitle_id for s in subtitles) == [20747, 20748, 20749, 137886]
    assert all(s.language == Language('hbs') for s in subtitles)


def test_series_not_found_returns_nothing(region, dexter_s01e01, requests_mock):
    requests_mock.get(f'{API_URL}/series?search=Dexter', json={'series': {'items': [], 'total': 0}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        assert provider.list_subtitles(dexter_s01e01, {Language('hrv')}) == []


def test_series_matched_by_tmdb_id_first(region, dexter_s01e01, requests_mock, data):
    dexter_s01e01.series_tmdb_id = 1405
    requests_mock.get(f'{API_URL}/series?tmdbId=1405', content=_load(data, 'prijevodi_series_search_dexter.json'))
    requests_mock.get(f'{API_URL}/series/116/episodes', content=_load(data, 'prijevodi_episodes_dexter_s01.json'))
    requests_mock.get(f'{API_URL}/translations/series?episodeId=6359', json=json.loads(
        _load(data, 'prijevodi_translations_dexter_s01e01.json')))

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert [s.subtitle_id for s in subtitles] == [TRANSLATION_HR]
    assert not any('search=' in r.url for r in requests_mock.request_history)
    dexter_s01e01.series_tmdb_id = None


def test_get_matches_release_group(region, dexter_s01e01, requests_mock, data):
    _mock_lookup(requests_mock, data)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    matches = subtitles[0].get_matches(dexter_s01e01)
    assert {'series', 'season', 'episode'} <= matches


# Paid translations

def test_paid_translation_hidden_by_default(region, dexter_s01e01, requests_mock, data):
    translations = _translations(data, {TRANSLATION_HR: {'behindTokens': True, 'price': 3.0}})
    _mock_lookup(requests_mock, data, translations)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert subtitles == []


def test_paid_translation_listed_when_allowed(region, dexter_s01e01, requests_mock, data):
    translations = _translations(data, {TRANSLATION_HR: {'behindTokens': True, 'price': 3.0}})
    _mock_lookup(requests_mock, data, translations)

    with PrijevodiOnlineProvider(api_key=API_KEY, allow_paid_translations=True) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert [s.subtitle_id for s in subtitles] == [TRANSLATION_HR]
    assert subtitles[0].paid is True
    assert subtitles[0].info.startswith('paid')


def test_purchased_paid_translation_listed_without_allowance(region, dexter_s01e01, requests_mock, data):
    translations = _translations(data, {TRANSLATION_HR: {'behindTokens': True, 'isPurchased': True}})
    _mock_lookup(requests_mock, data, translations)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert [s.subtitle_id for s in subtitles] == [TRANSLATION_HR]
    assert subtitles[0].paid is False


def test_paid_download_requests_ticket_and_charges_tokens(region, dexter_s01e01, requests_mock, data):
    translations = _translations(data, {TRANSLATION_HR: {'behindTokens': True, 'price': 3.0}})
    _mock_lookup(requests_mock, data, translations)
    requests_mock.post(f'{API_URL}/downloads/ticket', json=_ticket_response(tokensSpent=3))
    requests_mock.get(f'{API_URL}/translations/series/{TRANSLATION_HR}/download?ticket=abc',
                      content=_load(data, 'prijevodi_sub_37143.zip'))

    with PrijevodiOnlineProvider(api_key=API_KEY, allow_paid_translations=True) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})
        provider.download_subtitle(subtitles[0])

    ticket_request = next(r for r in requests_mock.request_history if r.method == 'POST')
    assert json.loads(ticket_request.body) == {'section': 'series', 'translationIds': [TRANSLATION_HR]}
    assert subtitles[0].content is not None


# Downloading

def test_download_subtitle_zip(region, dexter_s01e01, requests_mock, data):
    _mock_lookup(requests_mock, data)
    requests_mock.post(f'{API_URL}/downloads/ticket', json=_ticket_response())
    requests_mock.get(f'{API_URL}/translations/series/{TRANSLATION_SR}/download?ticket=abc',
                      content=_load(data, 'prijevodi_sub_37143.zip'))

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('srp')})
        provider.download_subtitle(subtitles[0])

    ticket_request = next(r for r in requests_mock.request_history if r.method == 'POST')
    assert json.loads(ticket_request.body) == {'section': 'series', 'translationIds': [TRANSLATION_SR]}
    assert ticket_request.headers['Authorization'] == f'Bearer {API_KEY}'
    download_request = requests_mock.request_history[-1]
    assert download_request.headers['Authorization'] == f'Bearer {API_KEY}'

    with zipfile.ZipFile(os.path.join(data, 'prijevodi_sub_37143.zip')) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(SUBTITLE_EXTENSIONS)]
        expected = fix_line_ending(zf.read(names[0]))

    assert subtitles[0].content == expected


@pytest.mark.parametrize('refusal, exception', [
    ({'reason': 'blocked', 'message': None, 'cause': 'vpn'}, IPAddressBlocked),
    ({'reason': 'temporarily_blocked', 'endsAt': None, 'message': None, 'cause': 'tor'}, IPAddressBlocked),
    ({'reason': 'cooldown', 'retryAfterSeconds': 600}, TooManyRequests),
    ({'reason': 'daily_cap', 'resetsAt': None, 'signedIn': True}, DownloadLimitExceeded),
    ({'reason': 'movie_cap', 'resetsAt': None, 'signedIn': True}, DownloadLimitExceeded),
    ({'reason': 'bulk_not_allowed'}, ProviderError),
])
def test_refused_ticket_maps_to_provider_exception(region, dexter_s01e01, requests_mock, data, refusal, exception):
    _mock_lookup(requests_mock, data)
    requests_mock.post(f'{API_URL}/downloads/ticket', json=_refused(refusal))

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('srp')})
        with pytest.raises(exception):
            provider.download_subtitle(subtitles[0])


def test_insufficient_tokens_raises_download_limit(region, dexter_s01e01, requests_mock, data):
    translations = _translations(data, {TRANSLATION_SR: {'behindTokens': True, 'price': 3.0}})
    _mock_lookup(requests_mock, data, translations)
    requests_mock.post(f'{API_URL}/downloads/ticket', status_code=400, json={
        'error': {'code': 'Tokens/InsufficientBalance', 'message': 'Not enough tokens'}})

    with PrijevodiOnlineProvider(api_key=API_KEY, allow_paid_translations=True) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('srp')})
        with pytest.raises(DownloadLimitExceeded, match='Tokens/InsufficientBalance'):
            provider.download_subtitle(subtitles[0])


def test_ticket_invalid_on_download_raises_provider_error(region, dexter_s01e01, requests_mock, data):
    _mock_lookup(requests_mock, data)
    requests_mock.post(f'{API_URL}/downloads/ticket', json=_ticket_response())
    requests_mock.get(f'{API_URL}/translations/series/{TRANSLATION_SR}/download?ticket=abc', status_code=403,
                      json={'error': {'code': 'Tracking/TicketInvalid', 'message': 'expired'}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('srp')})
        with pytest.raises(ProviderError, match='ticket rejected'):
            provider.download_subtitle(subtitles[0])


# Movies

MOVIE_TRANSLATION_HR = 578


@pytest.fixture(scope="session")
def inception():
    return Movie(
        "Inception.2010.720p.BluRay.x264-CROSSBOW.mkv",
        "Inception",
        2010,
        release_group="CROSSBOW",
        resolution="720p",
    )


def _movie_translations(data, changes):
    """Load the recorded Inception translations, changing the fields of the given translation ids.

    :param dict changes: Mapping of translation id to the fields to override on that item.
    """
    payload = json.loads(_load(data, 'prijevodi_movie_translations_inception.json'))
    for item in payload['movieTranslations']['items']:
        item.update(changes.get(item['id'], {}))
    return payload


def _mock_movie_lookup(requests_mock, data, translations=None):
    """Register the movie search and translation routes for Inception (movie id 324)."""
    requests_mock.get(f'{API_URL}/movies?search=Inception',
                      content=_load(data, 'prijevodi_movies_search_inception.json'))
    requests_mock.get(f'{API_URL}/translations/movies?movieId=324', json=translations or json.loads(
        _load(data, 'prijevodi_movie_translations_inception.json')))


def test_movie_paid_translation_hidden_by_default(region, inception, requests_mock, data):
    _mock_movie_lookup(requests_mock, data)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        assert provider.list_subtitles(inception, {Language('hrv')}) == []


def test_movie_paid_translation_listed_when_allowed(region, inception, requests_mock, data):
    _mock_movie_lookup(requests_mock, data)

    with PrijevodiOnlineProvider(api_key=API_KEY, allow_paid_translations=True) as provider:
        subtitles = provider.list_subtitles(inception, {Language('hrv')})

    assert [s.subtitle_id for s in subtitles] == [MOVIE_TRANSLATION_HR]
    assert subtitles[0].titles[0] == 'Inception'
    assert subtitles[0].year == 2010
    assert subtitles[0].paid is True
    assert subtitles[0].releases == ['Inception.720p.BluRay.x264CROSSBOW']


def test_movie_free_translation_listed_by_default(region, inception, requests_mock, data):
    translations = _movie_translations(data, {MOVIE_TRANSLATION_HR: {'behindTokens': False}})
    _mock_movie_lookup(requests_mock, data, translations)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(inception, {Language('hrv')})

    assert [s.subtitle_id for s in subtitles] == [MOVIE_TRANSLATION_HR]
    assert subtitles[0].paid is False


def test_movie_matched_by_tmdb_id_first(region, inception, requests_mock, data):
    inception.tmdb_id = 27205
    requests_mock.get(f'{API_URL}/movies?tmdbId=27205', content=_load(data, 'prijevodi_movies_search_inception.json'))
    requests_mock.get(f'{API_URL}/translations/movies?movieId=324', json=_movie_translations(
        data, {MOVIE_TRANSLATION_HR: {'behindTokens': False}}))

    try:
        with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
            subtitles = provider.list_subtitles(inception, {Language('hrv')})
    finally:
        inception.tmdb_id = None

    assert [s.subtitle_id for s in subtitles] == [MOVIE_TRANSLATION_HR]
    assert not any('search=' in r.url for r in requests_mock.request_history)


def test_movie_year_mismatch_is_not_matched(region, requests_mock, data):
    _mock_movie_lookup(requests_mock, data)
    other = Movie("Inception.1990.mkv", "Inception", 1990)

    with PrijevodiOnlineProvider(api_key=API_KEY, allow_paid_translations=True) as provider:
        assert provider.list_subtitles(other, {Language('hrv')}) == []


def test_movie_not_found_returns_nothing(region, inception, requests_mock):
    requests_mock.get(f'{API_URL}/movies?search=Inception', json={'movies': {'items': [], 'total': 0}})

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        assert provider.list_subtitles(inception, {Language('hrv')}) == []


def test_movie_matches_title_year_and_release(region, inception, requests_mock, data):
    translations = _movie_translations(data, {MOVIE_TRANSLATION_HR: {'behindTokens': False}})
    _mock_movie_lookup(requests_mock, data, translations)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(inception, {Language('hrv')})

    # The site writes the group glued to the codec (x264CROSSBOW), so guessit does not report a release group.
    matches = subtitles[0].get_matches(inception)
    assert {'title', 'year', 'resolution'} <= matches


def test_movie_paid_download_requests_movie_ticket(region, inception, requests_mock, data):
    _mock_movie_lookup(requests_mock, data)
    requests_mock.post(f'{API_URL}/downloads/ticket', json=_ticket_response(tokensSpent=1))
    requests_mock.get(f'{API_URL}/translations/movies/{MOVIE_TRANSLATION_HR}/download?ticket=abc',
                      content=_load(data, 'prijevodi_sub_37143.zip'))

    with PrijevodiOnlineProvider(api_key=API_KEY, allow_paid_translations=True) as provider:
        subtitles = provider.list_subtitles(inception, {Language('hrv')})
        provider.download_subtitle(subtitles[0])

    ticket_request = next(r for r in requests_mock.request_history if r.method == 'POST')
    assert json.loads(ticket_request.body) == {'section': 'movie', 'translationIds': [MOVIE_TRANSLATION_HR]}
    assert requests_mock.request_history[-1].headers['Authorization'] == f'Bearer {API_KEY}'
    assert subtitles[0].content is not None


# Matching is computed from the site's data, not from the video used for the lookup

def test_episode_matches_site_identity(region, dexter_s01e01, requests_mock, data):
    dexter_s01e01.series_imdb_id = 'tt0773262'
    _mock_lookup(requests_mock, data)

    try:
        with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
            subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})
        matches = subtitles[0].get_matches(dexter_s01e01)
    finally:
        dexter_s01e01.series_imdb_id = None

    assert {'series_imdb_id', 'series', 'season', 'episode'} <= matches


def test_episode_wrong_season_is_not_matched(region, requests_mock, data):
    _mock_lookup(requests_mock, data)
    other_season = Episode("Dexter.S02E05.720p.BluRay.x264-DEMAND.mkv", "Dexter", 2, 5)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(Episode("Dexter.S01E01.mkv", "Dexter", 1, 1), {Language('hrv')})

    matches = subtitles[0].get_matches(other_season)
    assert 'season' not in matches
    assert 'episode' not in matches
    assert 'series' in matches


def test_movie_matches_site_imdb_id(region, requests_mock, data):
    _mock_movie_lookup(requests_mock, data, _movie_translations(data, {MOVIE_TRANSLATION_HR: {'behindTokens': False}}))
    movie = Movie("Inception.1990.mkv", "Inception", 1990, imdb_id='tt1375666')

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(movie, {Language('hrv')})

    matches = subtitles[0].get_matches(movie)
    assert 'imdb_id' in matches
    assert 'title' in matches
    assert 'year' not in matches


def test_movie_wrong_year_and_title_are_not_matched(region, requests_mock, data):
    _mock_movie_lookup(requests_mock, data, _movie_translations(data, {MOVIE_TRANSLATION_HR: {'behindTokens': False}}))
    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(Movie("Inception.mkv", "Inception", 2010), {Language('hrv')})

    other = Movie("Something.Else.1990.mkv", "Something Else", 1990)
    matches = subtitles[0].get_matches(other)
    assert 'title' not in matches
    assert 'year' not in matches
    assert 'imdb_id' not in matches


def test_movie_score_reflects_site_identity(region, requests_mock, data):
    _mock_movie_lookup(requests_mock, data, _movie_translations(data, {MOVIE_TRANSLATION_HR: {'behindTokens': False}}))
    right = Movie("Inception.2010.720p.BluRay.x264-CROSSBOW.mkv", "Inception", 2010, imdb_id='tt1375666')
    wrong_year = Movie("Inception.1990.720p.BluRay.x264-CROSSBOW.mkv", "Inception", 1990)

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(right, {Language('hrv')})

    subtitle = subtitles[0]
    assert compute_score(subtitle, right) > compute_score(subtitle, wrong_year)
    assert 'year' not in subtitle.get_matches(wrong_year)


# Dropped connections: lookups are repeated, tickets and downloads are not

@pytest.fixture
def no_retry_delay(monkeypatch):
    monkeypatch.setattr(prijevodionline_module, 'RETRY_DELAY_SECONDS', 0)


def test_lookup_retries_a_dropped_connection(region, dexter_s01e01, requests_mock, data, no_retry_delay):
    dropped = requests.exceptions.ConnectionError("('Connection aborted.', RemoteDisconnected('Remote end closed'))")
    requests_mock.get(f'{API_URL}/series?search=Dexter', [
        {'exc': dropped},
        {'content': _load(data, 'prijevodi_series_search_dexter.json')},
    ])
    requests_mock.get(f'{API_URL}/series/116/episodes', content=_load(data, 'prijevodi_episodes_dexter_s01.json'))
    requests_mock.get(f'{API_URL}/translations/series?episodeId=6359', json=json.loads(
        _load(data, 'prijevodi_translations_dexter_s01e01.json')))

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert [s.subtitle_id for s in subtitles] == [TRANSLATION_HR]
    assert sum(1 for r in requests_mock.request_history if 'search=Dexter' in r.url) == 2


def test_lookup_gives_up_after_repeated_drops(region, dexter_s01e01, requests_mock, no_retry_delay):
    requests_mock.get(f'{API_URL}/series?search=Dexter',
                      exc=requests.exceptions.ConnectionError('Remote end closed'))

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        with pytest.raises(requests.exceptions.ConnectionError):
            provider.list_subtitles(dexter_s01e01, {Language('hrv')})

    assert sum(1 for r in requests_mock.request_history if 'search=Dexter' in r.url) == prijevodionline_module.LOOKUP_ATTEMPTS


def test_ticket_is_not_repeated_after_a_dropped_connection(region, dexter_s01e01, requests_mock, data, no_retry_delay):
    _mock_lookup(requests_mock, data)
    requests_mock.post(f'{API_URL}/downloads/ticket', exc=requests.exceptions.ConnectionError('Remote end closed'))

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('srp')})
        with pytest.raises(requests.exceptions.ConnectionError):
            provider.download_subtitle(subtitles[0])

    assert sum(1 for r in requests_mock.request_history if r.method == 'POST') == 1


def test_download_is_not_repeated_after_a_dropped_connection(region, dexter_s01e01, requests_mock, data,
                                                              no_retry_delay):
    _mock_lookup(requests_mock, data)
    requests_mock.post(f'{API_URL}/downloads/ticket', json=_ticket_response())
    requests_mock.get(f'{API_URL}/translations/series/{TRANSLATION_SR}/download?ticket=abc',
                      exc=requests.exceptions.ConnectionError('Remote end closed'))

    with PrijevodiOnlineProvider(api_key=API_KEY) as provider:
        subtitles = provider.list_subtitles(dexter_s01e01, {Language('srp')})
        with pytest.raises(requests.exceptions.ConnectionError):
            provider.download_subtitle(subtitles[0])

    assert sum(1 for r in requests_mock.request_history if r.method == 'GET' and '/download' in r.url) == 1
