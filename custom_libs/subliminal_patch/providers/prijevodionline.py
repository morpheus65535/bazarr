# -*- coding: utf-8 -*-
import io
import logging
import os
import re
import time
from typing import Any, NoReturn
from zipfile import ZipFile, is_zipfile

import requests
from guessit import guessit
from rarfile import RarFile, is_rarfile
from requests import Session
from subzero.language import Language

from subliminal.exceptions import (AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError,
                                   ServiceUnavailable)
from subliminal.providers import Provider
from subliminal.subtitle import SUBTITLE_EXTENSIONS, Subtitle, fix_line_ending
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import ForbiddenError, IPAddressBlocked, ParseResponseError, TooManyRequests
from subliminal_patch.subtitle import guess_matches

logger = logging.getLogger(__name__)

API_KEY_PREFIX = 'po_'

# Read-only lookups are retried when the connection drops, which the server does for idle keep-alive connections.
LOOKUP_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2.0

# Site language codes (see GET /api/v1/languages) mapped to Bazarr languages.
SITE_LANGUAGES = {
    'hr': Language('hrv'),
    'sr': Language('srp'),
    'sr-cyr': Language('srp'),
    'cnr': Language('mne'),
    'bs': Language('bos'),
}


# Ticket section of each translation kind, mapped to the API path that serves its file.
DOWNLOAD_PATHS = {'series': 'translations/series', 'movie': 'translations/movies'}


class PrijevodiOnlineSubtitle(Subtitle):
    """Prijevodi-Online translation of an episode (section ``series``) or a movie (section ``movie``).

    ``titles``, ``year``, ``imdb_id`` and ``tmdb_id`` hold the identity of the series or movie on the site.
    ``season`` and ``episode`` are set only for episode translations.
    """
    provider_name = 'prijevodionline'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language: Language, page_link: str, subtitle_id: int, section: str, titles: list[str],
                 year: int | None, imdb_id: str | None, tmdb_id: int | None, releases: list[str],
                 hearing_impaired: bool, paid: bool, price: float | None, season: int | None = None,
                 episode: int | None = None) -> None:
        """Store the translation and the identity of its series or movie on the site.

        :param Language language: Bazarr language of the translation.
        :param str page_link: Download URL of the translation, without the ticket.
        :param int subtitle_id: Translation id on the site.
        :param str section: ``series`` for episodes or ``movie`` for movies.
        :param list[str] titles: Title and original title of the series or movie, as known to the site.
        :param int | None year: Premiere year of the series, or release year of the movie.
        :param str | None imdb_id: IMDb id of the series or movie on the site.
        :param int | None tmdb_id: TMDB id of the series or movie on the site.
        :param list[str] releases: Release names taken from the translation.
        :param bool hearing_impaired: Whether the translation is for the hearing impaired.
        :param bool paid: Whether downloading the translation spends tokens.
        :param float | None price: Token price of a paid translation, if known.
        :param int | None season: Season number, for episode translations.
        :param int | None episode: Episode number, for episode translations.
        :raises ValueError: If ``section`` is not a known translation kind.
        """
        if section not in DOWNLOAD_PATHS:
            raise ValueError(f'Unknown Prijevodi-Online section {section!r}')
        super().__init__(language, hearing_impaired=hearing_impaired, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.section = section
        self.titles = [name for name in titles if name]
        self.year = year
        self.imdb_id = imdb_id
        self.tmdb_id = tmdb_id
        self.season = season
        self.episode = episode
        self.releases = releases
        self.release_info = ', '.join(releases)
        self.paid = paid
        self.price = price

    @property
    def download_path(self) -> str:
        """API path that serves the translation file, relative to ``api_url``."""
        return DOWNLOAD_PATHS[self.section]

    @property
    def id(self) -> str:
        """Translation id on the site."""
        return str(self.subtitle_id)

    @property
    def info(self) -> str:
        """Text shown in the search results: a paid marker followed by the release names."""
        parts = ['paid'] if self.paid else []
        if self.release_info:
            parts.append(self.release_info)
        return ', '.join(parts)

    def get_matches(self, video: Episode | Movie) -> set[str]:
        """Return the matches between this subtitle and the video.

        Every match is computed by comparing the site's data with the video. Nothing is assumed from the
        lookup that produced the subtitle. An episode translation only matches an episode and a movie
        translation only matches a movie.

        :param video: Episode or movie being searched.
        :return: Names of the matched attributes.
        """
        if isinstance(video, Episode) and self.section == 'series':
            return self._episode_matches(video)
        if isinstance(video, Movie) and self.section == 'movie':
            return self._movie_matches(video)
        return set()

    def _episode_matches(self, video: Episode) -> set[str]:
        """Return the matches between this episode translation and an episode.

        :param Episode video: Episode being searched.
        :return: Names of the matched attributes.
        """
        matches: set[str] = set()
        if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
            matches.add('series_imdb_id')
        if video.series_tmdb_id and self.tmdb_id and str(video.series_tmdb_id) == str(self.tmdb_id):
            matches.add('series_tmdb_id')

        wanted_titles = {sanitize(name) for name in [video.series] + video.alternative_series if name}
        if wanted_titles & {sanitize(name) for name in self.titles}:
            matches.add('series')
        if video.year and self.year == video.year:
            matches.add('year')
        if video.season and self.season == video.season:
            matches.add('season')
        if video.episode and self.episode == video.episode:
            matches.add('episode')

        for release in self.releases:
            matches |= guess_matches(video, guessit(release, {'type': 'episode'}))
        return matches

    def _movie_matches(self, video: Movie) -> set[str]:
        """Return the matches between this movie translation and a movie.

        :param Movie video: Movie being searched.
        :return: Names of the matched attributes.
        """
        matches: set[str] = set()
        if video.imdb_id and self.imdb_id == video.imdb_id:
            matches.add('imdb_id')
        if video.tmdb_id and self.tmdb_id and str(video.tmdb_id) == str(self.tmdb_id):
            matches.add('tmdb_id')

        wanted_titles = {sanitize(name) for name in [video.title] + video.alternative_titles if name}
        if wanted_titles & {sanitize(name) for name in self.titles}:
            matches.add('title')
        if video.year and self.year == video.year:
            matches.add('year')

        for release in self.releases:
            matches |= guess_matches(video, guessit(release, {'type': 'movie'}))
        return matches


class PrijevodiOnlineProvider(Provider):
    """Prijevodi-Online provider using the documented API with a bearer API key.

    Episodes use series translations and movies use movie translations. Paid translations are only
    listed and downloaded when ``allow_paid_translations`` is enabled. Their download ticket charges the
    account tokens.
    """
    languages = {Language('hrv'), Language('mne'), Language('srp'), Language('bos'), Language('hbs')}
    video_types = (Episode, Movie)
    server_url = 'https://www.prijevodi-online.org'
    api_url = server_url + '/api/v1'
    # Required by the provider registry, which patches the subtitle base classes from this attribute.
    subtitle_class = PrijevodiOnlineSubtitle

    def __init__(self, api_key: str | None = None, allow_paid_translations: bool = False) -> None:
        """Validate the API key format before any request is made.

        A missing or malformed key raises :class:`ConfigurationError` without contacting the API, so the
        throttle recorded by Bazarr is the only thing that retries it.

        :param str | None api_key: API key, in the form ``po_...``.
        :param bool allow_paid_translations: Whether paid translations may be listed and downloaded.
        :raises ConfigurationError: If the key is missing or not in the documented form.
        """
        key = (api_key or '').strip()
        if not key:
            raise ConfigurationError('Prijevodi-Online API key is not set')
        if not key.startswith(API_KEY_PREFIX):
            raise ConfigurationError('Prijevodi-Online API key must start with "po_"')

        self.api_key = key
        self.allow_paid_translations = bool(allow_paid_translations)
        self.session: Session | None = None

    def initialize(self) -> None:
        """Create the HTTP session that sends the bearer API key and the Bazarr user agent."""
        self.session = Session()
        self.session.headers['Authorization'] = f'Bearer {self.api_key}'
        self.session.headers['Accept'] = 'application/json'
        self.session.headers['User-Agent'] = os.environ.get('SZ_USER_AGENT', 'Bazarr')

    def terminate(self) -> None:
        """Close the HTTP session."""
        if self.session is not None:
            self.session.close()

    def _send(self, method: str, path: str, *, retry: bool = False, **kwargs: Any) -> requests.Response:
        """Send a request to the API and raise a provider exception for any error response.

        Only requests marked ``retry`` are repeated after a dropped connection or a timeout. Ticket requests
        and downloads are not repeated, because the server may already have processed them: a repeated
        ticket request can charge tokens twice and a repeated download fails on an already used ticket.

        :param str method: HTTP method.
        :param str path: API path relative to ``api_url``.
        :param bool retry: Whether the request is a read-only lookup that may be repeated.
        :return: The successful response.
        """
        if self.session is None:
            raise ProviderError('Prijevodi-Online provider is not initialized')
        kwargs.setdefault('timeout', 15)
        attempts = LOOKUP_ATTEMPTS if retry else 1
        for attempt in range(1, attempts + 1):
            try:
                r = self.session.request(method, self.api_url + path, **kwargs)
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
                if attempt == attempts:
                    raise
                logger.debug('Prijevodi-Online %s %s failed (%s), retrying (attempt %d of %d)', method, path,
                             error, attempt + 1, attempts)
                time.sleep(RETRY_DELAY_SECONDS * attempt)
        if r.status_code >= 400:
            raise self._api_error(r)
        return r

    @staticmethod
    def _json(r: requests.Response) -> dict[str, Any]:
        """Decode a JSON object body.

        :param requests.Response r: Successful response.
        :return: The decoded object.
        """
        try:
            data = r.json()
        except ValueError as error:
            raise ParseResponseError('Prijevodi-Online returned a body that is not JSON') from error
        if not isinstance(data, dict):
            raise ParseResponseError('Prijevodi-Online returned an unexpected JSON body')
        return data

    @staticmethod
    def _error_details(r: requests.Response) -> tuple[str, str]:
        """Read the ``code`` and ``message`` of an error response.

        :param requests.Response r: Error response.
        :return: The error code and message, both empty when the body has no error object.
        """
        try:
            body = r.json()
        except ValueError:
            return '', r.text[:200]
        error = body.get('error') if isinstance(body, dict) else None
        if not isinstance(error, dict):
            return '', r.text[:200]
        return str(error.get('code') or ''), str(error.get('message') or '')

    def _api_error(self, r: requests.Response) -> Exception:
        """Map an API error response to the exception Bazarr uses for throttling.

        Authentication and subscription failures (401) become :class:`AuthenticationError`, which Bazarr
        throttles for a long time and clears when the API key is changed. A key without the grant a route
        needs (403) becomes :class:`ForbiddenError`, which is throttled for a shorter time.

        :param requests.Response r: Error response.
        :return: The exception to raise.
        """
        code, message = self._error_details(r)
        status = r.status_code
        detail = f'HTTP {status} {code}: {message}'.strip()

        if status == 401:
            return AuthenticationError(f'Prijevodi-Online rejected the API key ({detail})')
        if status == 403 and code == 'Tracking/TicketInvalid':
            return ProviderError(f'Prijevodi-Online download ticket rejected ({detail})')
        if status == 403:
            return ForbiddenError(f'Prijevodi-Online API key lacks the required permission ({detail})')
        if status == 429:
            return TooManyRequests(f'Prijevodi-Online rate limit reached, Retry-After '
                                   f'{r.headers.get("Retry-After", "unknown")} seconds')
        if status == 503:
            return ServiceUnavailable(f'Prijevodi-Online is unavailable ({detail})')
        if code in ('Tokens/InsufficientBalance', 'Tokens/SpendLocked'):
            return DownloadLimitExceeded(f'Prijevodi-Online tokens cannot be spent ({detail})')
        return ProviderError(f'Prijevodi-Online API error ({detail})')

    def _get_items(self, path: str, key: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Collect every item of a paginated list endpoint.

        :param str path: API path relative to ``api_url``.
        :param str key: Top-level key wrapping the list in the response.
        :param dict params: Query parameters, merged with the paging parameters.
        :return: All items returned by the endpoint.
        """
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            data = self._json(self._send('GET', path, retry=True,
                                         params={**params, 'page': page, 'perPage': 100}))[key]
            items.extend(data['items'])
            if not data['items'] or len(items) >= data['total']:
                return items
            page += 1

    @staticmethod
    def _year_matches(year: int | None, release_date: str | None) -> bool:
        """Compare a video year with the release date of a site item.

        A year that is unknown on either side does not exclude the item.

        :param int | None year: Year of the video.
        :param str | None release_date: Release date in ``YYYY-MM-DD`` form.
        :return: ``False`` only when both years are known and differ.
        """
        if not year or not release_date:
            return True
        return str(release_date)[:4] == str(year)

    def _find_series(self, video: Episode) -> dict[str, Any] | None:
        """Find a series, preferring a TMDB id match, then an IMDb id match, then a title match.

        :param Episode video: Episode being searched.
        :return: The series item from the search results, or ``None``.
        """
        if video.series_tmdb_id:
            for item in self._get_items('/series', 'series', {'tmdbId': video.series_tmdb_id}):
                if str(item['tmdbId']) == str(video.series_tmdb_id):
                    return item

        for title in [video.series] + video.alternative_series:
            items = self._get_items('/series', 'series', {'search': title})
            if video.series_imdb_id:
                for item in items:
                    if item['imdbId'] == video.series_imdb_id:
                        return item
            sanitized_title = sanitize(title)
            for item in items:
                if sanitized_title in (sanitize(item['title']), sanitize(item['originalTitle'] or '')):
                    return item
        return None

    def _find_movie(self, video: Movie) -> dict[str, Any] | None:
        """Find a movie, preferring a TMDB id match, then an IMDb id match, then a title and year match.

        :param Movie video: Movie being searched.
        :return: The movie item from the search results, or ``None``.
        """
        if video.tmdb_id:
            for item in self._get_items('/movies', 'movies', {'tmdbId': video.tmdb_id}):
                if str(item['tmdbId']) == str(video.tmdb_id):
                    return item

        for title in [video.title] + video.alternative_titles:
            items = self._get_items('/movies', 'movies', {'search': title})
            if video.imdb_id:
                for item in items:
                    if item['imdbId'] == video.imdb_id:
                        return item
            sanitized_title = sanitize(title)
            for item in items:
                if (sanitized_title in (sanitize(item['title']), sanitize(item['originalTitle'] or ''))
                        and self._year_matches(video.year, item['releaseDate'])):
                    return item
        return None

    def _find_episode(self, series_id: int, season: int, episode: int) -> dict[str, Any] | None:
        """Find an episode of a series by season and episode number.

        The episodes route returns the whole series in one response.

        :param int series_id: Series id on the site.
        :param int season: Season number.
        :param int episode: Episode number.
        :return: The episode item, or ``None``.
        """
        data = self._json(self._send('GET', f'/series/{series_id}/episodes', retry=True))['episodes']
        for item in data['items']:
            if item['seasonNumber'] == season and item['episodeNumber'] == episode:
                return item
        return None

    def _usable_language(self, item: dict[str, Any], languages: set[Language]) -> tuple[Language, bool] | None:
        """Decide whether a translation item is offered for the requested languages.

        Only approved, published, non-revoked translations are kept. Paid translations that are not
        purchased are kept only when paid translations are allowed.

        :param dict item: Translation item from the API.
        :param set languages: Requested Bazarr languages.
        :return: The Bazarr language and whether the translation is paid, or ``None`` when it is skipped.
        """
        if item['status'] != 'approved' or item['isRevoked'] or not item['isPublished']:
            return None

        paid = bool(item['behindTokens']) and not item['isPurchased']
        if paid and not self.allow_paid_translations:
            return None

        sub_lang = SITE_LANGUAGES.get(item['languageCode'] or '')
        if sub_lang is None:
            return None
        if sub_lang not in languages and Language('hbs') not in languages:
            return None
        if Language('hbs') in languages:
            sub_lang = Language('hbs')
        return sub_lang, paid

    @staticmethod
    def _year_of(release_date: str | None) -> int | None:
        """Return the year of a ``YYYY-MM-DD`` date from the API.

        :param str | None release_date: Date from the API, possibly missing.
        :return: The year, or ``None`` when the date is missing or malformed.
        """
        if not release_date:
            return None
        try:
            return int(str(release_date)[:4])
        except ValueError:
            return None

    def _episode_subtitles_from_items(self, items: list[dict[str, Any]], languages: set[Language],
                                      series: dict[str, Any]) -> list[PrijevodiOnlineSubtitle]:
        """Convert series translation items into subtitles for the requested languages.

        :param list items: Translation items from the API.
        :param set languages: Requested Bazarr languages.
        :param dict series: The series item the translations belong to.
        :return: The matching subtitles.
        """
        subtitles = []
        for item in items:
            usable = self._usable_language(item, languages)
            if usable is None:
                continue
            sub_lang, paid = usable
            releases = [r.strip() for r in re.split(r'[/\r\n]+', item['description'] or '') if r.strip()]
            subtitles.append(self.subtitle_class(
                sub_lang, f"{self.api_url}/translations/series/{item['id']}/download", item['id'],
                section='series', titles=[item['seriesTitle'], item['seriesOriginalTitle']],
                year=self._year_of(series.get('premiereDate')), imdb_id=series.get('imdbId'),
                tmdb_id=series.get('tmdbId'), releases=releases, hearing_impaired=bool(item['hearingImpaired']),
                paid=paid, price=item['price'], season=item['seasonNumber'], episode=item['episodeNumber'],
            ))
        return subtitles

    @staticmethod
    def _movie_release_names(item: dict[str, Any]) -> list[str]:
        """Return the release name of a movie translation.

        The ``title`` field holds the release name (``Inception.720p.BluRay.x264CROSSBOW.zip``). The
        ``fileName`` field is the uploaded subtitle archive and is only used when ``title`` is empty.

        :param dict item: Movie translation item from the API.
        :return: The release name without the archive extension, or an empty list.
        """
        for field in ('title', 'fileName'):
            name = re.sub(r'\.(zip|rar)$', '', item.get(field) or '', flags=re.IGNORECASE).strip()
            if name:
                return [name]
        return [item['releaseFormatName']] if item.get('releaseFormatName') else []

    def _movie_subtitles_from_items(self, items: list[dict[str, Any]], languages: set[Language],
                                    movie: dict[str, Any]) -> list[PrijevodiOnlineSubtitle]:
        """Convert movie translation items into subtitles for the requested languages.

        :param list items: Movie translation items from the API.
        :param set languages: Requested Bazarr languages.
        :param dict movie: The movie item the translations belong to.
        :return: The matching subtitles.
        """
        subtitles = []
        for item in items:
            usable = self._usable_language(item, languages)
            if usable is None:
                continue
            sub_lang, paid = usable
            subtitles.append(self.subtitle_class(
                sub_lang, f"{self.api_url}/translations/movies/{item['id']}/download", item['id'],
                section='movie', titles=[item['movieTitle'], item['movieOriginalTitle']], year=item['movieYear'],
                imdb_id=movie.get('imdbId'), tmdb_id=movie.get('tmdbId'), releases=self._movie_release_names(item),
                hearing_impaired=bool(item['hearingImpaired']), paid=paid, price=item['price'],
            ))
        return subtitles

    def _list_episode_subtitles(self, video: Episode,
                                languages: set[Language]) -> list[PrijevodiOnlineSubtitle]:
        """Search the API for subtitles of an episode.

        :param Episode video: Episode to search for.
        :param set languages: Requested Bazarr languages.
        :return: The matching subtitles.
        """
        series = self._find_series(video)
        if not series:
            logger.debug('Series %r not found on prijevodi-online', video.series)
            return []

        episode = self._find_episode(series['id'], video.season, video.episode)
        if not episode:
            logger.debug('S%02dE%02d not found for series %r', video.season, video.episode, video.series)
            return []

        items = self._get_items('/translations/series', 'translations', {'episodeId': episode['id']})
        subtitles = self._episode_subtitles_from_items(items, languages, series)
        logger.debug('Found %d subtitle(s) for %r S%02dE%02d', len(subtitles), video.series, video.season,
                     video.episode)
        return subtitles

    def _list_movie_subtitles(self, video: Movie, languages: set[Language]) -> list[PrijevodiOnlineSubtitle]:
        """Search the API for subtitles of a movie.

        :param Movie video: Movie to search for.
        :param set languages: Requested Bazarr languages.
        :return: The matching subtitles.
        """
        movie = self._find_movie(video)
        if not movie:
            logger.debug('Movie %r not found on prijevodi-online', video.title)
            return []

        items = self._get_items('/translations/movies', 'movieTranslations', {'movieId': movie['id']})
        subtitles = self._movie_subtitles_from_items(items, languages, movie)
        logger.debug('Found %d subtitle(s) for movie %r', len(subtitles), video.title)
        return subtitles

    def list_subtitles(self, video: Episode | Movie, languages: set[Language]) -> list[PrijevodiOnlineSubtitle]:
        """Search the API for subtitles of an episode or a movie.

        :param video: Episode or movie to search for. Other video types return nothing.
        :param set languages: Requested Bazarr languages.
        :return: The matching subtitles.
        """
        if isinstance(video, Episode):
            return self._list_episode_subtitles(video, languages)
        if isinstance(video, Movie):
            return self._list_movie_subtitles(video, languages)
        return []

    @staticmethod
    def _raise_for_refusal(refusal: dict[str, Any]) -> NoReturn:
        """Translate a download refusal from the API into a provider exception.

        :param dict refusal: The ``refusal`` object of a refused ticket response.
        """
        reason = refusal.get('reason')
        if reason == 'cooldown':
            raise TooManyRequests(f"Prijevodi-Online download cooldown: retry after "
                                  f"{refusal.get('retryAfterSeconds')} seconds")
        if reason in ('daily_cap', 'movie_cap'):
            raise DownloadLimitExceeded(f"Prijevodi-Online {reason} reached, resets at {refusal.get('resetsAt')}")
        if reason in ('blocked', 'temporarily_blocked'):
            raise IPAddressBlocked(f"Prijevodi-Online blocked downloads ({reason}, cause "
                                   f"{refusal.get('cause')}): {refusal.get('message')}")
        raise ProviderError(f'Prijevodi-Online refused the download: {reason}')

    def _request_ticket(self, section: str, translation_id: int) -> str:
        """Request a one-minute download ticket for a translation.

        For a paid translation that is not purchased, the API charges the account tokens when the ticket
        is issued.

        :param str section: ``series`` or ``movie``, as expected by the ticket route.
        :param int translation_id: Translation id on the site.
        :return: The ticket to pass to the download endpoint.
        """
        r = self._send('POST', '/downloads/ticket', json={'section': section, 'translationIds': [translation_id]})
        outcome = self._json(r)['download']
        if outcome.get('outcome') == 'ticket':
            if outcome.get('tokensSpent'):
                logger.info('Prijevodi-Online spent %s token(s) on translation %s', outcome['tokensSpent'],
                            translation_id)
            return outcome['ticket']
        self._raise_for_refusal(outcome.get('refusal') or {})

    @staticmethod
    def _extract_subtitle(data: bytes, name: str) -> bytes:
        """Extract the first subtitle file from a rar or zip archive.

        :param bytes data: Archive content.
        :param str name: Translation id, used in error messages.
        :return: The subtitle content with normalized line endings.
        """
        archive_stream = io.BytesIO(data)
        if is_rarfile(archive_stream):
            logger.debug('Identified rar archive')
            archive_stream.seek(0)
            with RarFile(archive_stream) as rf:
                names = [n for n in rf.namelist() if n.lower().endswith(SUBTITLE_EXTENSIONS)]
                if not names:
                    raise ProviderError('No subtitle file found in rar archive')
                return fix_line_ending(rf.read(names[0]))
        if is_zipfile(archive_stream):
            logger.debug('Identified zip archive')
            archive_stream.seek(0)
            with ZipFile(archive_stream) as zf:
                names = [n for n in zf.namelist() if n.lower().endswith(SUBTITLE_EXTENSIONS)]
                if not names:
                    raise ProviderError('No subtitle file found in zip archive')
                return fix_line_ending(zf.read(names[0]))
        raise ProviderError(f'Unrecognized archive format for subtitle {name}')

    def download_subtitle(self, subtitle: PrijevodiOnlineSubtitle) -> None:
        """Request a ticket for the translation, download the archive and extract the subtitle.

        :param PrijevodiOnlineSubtitle subtitle: Subtitle to download. Its content is set on success.
        """
        logger.info('Downloading subtitle %r', subtitle)
        ticket = self._request_ticket(subtitle.section, subtitle.subtitle_id)
        r = self._send('GET', f'/{subtitle.download_path}/{subtitle.subtitle_id}/download',
                       params={'ticket': ticket}, timeout=30)
        subtitle.content = self._extract_subtitle(r.content, subtitle.id)
