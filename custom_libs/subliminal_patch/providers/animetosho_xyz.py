# -*- coding: utf-8 -*-
import functools
import logging
import lzma
import os
import re
from typing import Callable

from guessit import guessit
from requests import Session, Response
from subzero.language import Language

from subliminal.exceptions import ProviderError
from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.video import Episode

logger = logging.getLogger(__name__)

supported_languages = [
    "ara",
    "eng",
    "fin",
    "fra",
    "deu",
    "heb",
    "ind",
    "ita",
    "jpn",
    "por",
    "pol",
    "rus",
    "spa",
    "swe",
    "tha",
    "tur",
    "vie",
]

_BRAZILIAN_PORTUGUESE_RE = re.compile(r'brazil|\bbr\b', re.IGNORECASE)


@functools.lru_cache(2048)
def _memoized_release_guess(release_name):
    # Guessit takes milliseconds per call and releases are re-parsed on every search of an episode,
    # while the same batch release is listed for every episode it contains.
    return guessit(release_name)


class AnimeToshoXYZSubtitle(Subtitle):
    provider_name = 'animetosho_xyz'

    def __init__(self, language, download_link, release_guesses, release_info, release_id, forced=False):
        # AnimeTosho reports the forced disposition flag of the subtitle track. Keep it on the
        # language so a forced (signs only) track is never offered as a normal subtitle.
        language = Language.rebuild(language, forced=forced)

        super(AnimeToshoXYZSubtitle, self).__init__(
            language,
            page_link=download_link,
        )
        # Parsed once per release and shared by all its subtitles so guessit runs once no matter
        # how many subtitle tracks a release carries.
        self.release_guesses = release_guesses
        self.download_link = download_link
        self.release_info = release_info
        self.release_id = release_id
        self.forced = forced
        self.matches = set()

    @property
    def id(self):
        # AnimeTosho may reuse the same attachment URL across releases; keep each
        # release association distinct so scoring can use release-specific metadata.
        return f'{self.release_id}:{self.download_link}'

    def get_matches(self, video):
        # AnimeTosho torrent names frequently append the Japanese or alternate title in parentheses
        # or after a pipe, which guessit mistakes for the release group. The file names of a release
        # are scene-style and carry the real metadata, so every parsed name has to be matched. #3612
        for release_guess in self.release_guesses:
            self.matches |= guess_matches(video, release_guess)

        # Add these data are explicit extracted from the API and they always have to match otherwise they wouldn't
        # arrive at this point and would stop on list_subtitles.
        self.matches.update(['series', 'season', 'episode'])

        return self.matches


class AnimeToshoXYZProvider(Provider, ProviderSubtitleArchiveMixin):
    provider_name = 'animetosho_xyz'
    subtitle_class = AnimeToshoXYZSubtitle
    languages = {Language('por', 'BR')} | {Language(sl) for sl in supported_languages}
    # The provider pool intersects the requested languages with the languages declared here before
    # calling list_subtitles, so the forced variants have to be declared as well or a profile
    # asking for forced subtitles would never reach this provider.
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    video_types = Episode

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers.update({'User-Agent': os.environ.get("SZ_USER_AGENT", "Bazarr")})

    def terminate(self):
        self.session.close()

    def checked(self, fn: Callable) -> Response:
        """
        Executes the provided function and performs error handling and response validation for API calls.

        :param fn: The callable function that makes the HTTP request.
        :type fn: Callable
        :return: The HTTP response object returned by the provided function if the status code is valid.
        :rtype: Response
        :raises ProviderError: If an unhandled exception occurs or the endpoint is not found.
        """
        response = None
        try:
            response = fn()
        except Exception:
            logger.exception('Unhandled exception raised.')
            raise ProviderError('Unhandled exception raised. Check log.')
        else:
            status_code = response.status_code
            if status_code == 404:
                logger.error(f"Endpoint not found: {response.url}")
                raise ProviderError("Endpoint not found")
            elif status_code != 200:
                logger.error(f"HTTP error {status_code} for {response.url}")
                raise ProviderError(f"HTTP error {status_code}")

            return response

    def list_subtitles(self, video, languages):
        if not video.series_anidb_episode_id:
            logger.debug('Skipping video %r. It is not an anime or the anidb_episode_id could not be identified', video)
            return []

        episode_id = video.series_anidb_episode_id
        if isinstance(episode_id, (list, tuple)):
            episode_id = episode_id[-1] if episode_id else None

        if not episode_id:
            return []

        return [s for s in self._get_series(episode_id) if s.language in languages]

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)

        r = self.checked(lambda: self.session.get(subtitle.page_link, timeout=10))

        if not self._is_xz_file(r.content):
            raise ProviderError('Unidentified archive type')

        subtitle.content = lzma.decompress(r.content)
        return subtitle

    @staticmethod
    def _is_xz_file(content):
        return content.startswith(b'\xFD\x37\x7A\x58\x5A\x00')

    def _get_series(self, episode_id):
        detail_api_url = 'https://feed.animetosho.xyz/json'

        subtitles = []
        entries = self._get_series_entries(episode_id)

        for entry in entries:
            r = self.checked(
                lambda: self.session.get(
                    detail_api_url,
                    params={
                        'show': 'torrent',
                        'id': entry['id'],
                    },
                    timeout=10
                )
            )

            torrent_data = r.json()
            # Copy the memoized guesses because guess_matches uses them as scratch space.
            release_guesses = [dict(_memoized_release_guess(release_name))
                               for release_name in self._release_names(torrent_data)]

            for subtitle_file in self._iter_subtitle_attachments(torrent_data):
                info = subtitle_file.get('info', {})
                lang_code = info.get('language_code', 'eng')
                lang = Language.fromalpha3b(lang_code)

                # Portuguese and Brazilian Portuguese share the same code, so the language name is
                # the only thing telling them apart. The API labels it "Portuguese[BR]", but the
                # spelled-out "Brazilian Portuguese" also shows up.
                if lang.alpha3 == 'por' and _BRAZILIAN_PORTUGUESE_RE.search(info.get('language', '')):
                    lang = Language('por', 'BR')

                subtitle = self.subtitle_class(
                    lang,
                    subtitle_file['url'],
                    release_guesses=release_guesses,
                    release_info=entry.get('title'),
                    release_id=torrent_data['id'],
                    # AnimeTosho exposes the forced disposition flag of the track as a boolean.
                    forced=bool(info.get('forced', False)),
                )

                logger.debug('Found subtitle %r', subtitle)
                subtitles.append(subtitle)

        return subtitles

    @staticmethod
    def _release_names(torrent_data):
        """Return the names carrying matchable release metadata.

        Only the primary file name is parsed: every file of a release carries the same metadata and
        running guessit over all the files of a large batch is expensive. The torrent name is kept
        as well because some releases do not list any file at all.
        """
        release_names = []
        files = [file for file in torrent_data.get('files') or [] if file.get('filename')]
        if files:
            primary_file_id = torrent_data.get('primary_file_id')
            primary_file = next((file for file in files if file.get('id') == primary_file_id), None)
            release_names.append((primary_file or files[0])['filename'])

        torrent_name = torrent_data.get('torrent_name')
        if torrent_name:
            release_names.append(torrent_name)

        return release_names

    @staticmethod
    def _iter_subtitle_attachments(torrent_data):
        """Yield the subtitle attachments of a release.

        AnimeTosho.xyz lists them either at the top level of the release ("attachments") or nested
        under each of its files ("files[].attachments"), depending on the release, so both shapes
        have to be collected. A release only ever uses one of them but the same attachment is
        still guarded against being yielded twice.
        """
        seen = set()

        def collect(attachments):
            for attachment in attachments or []:
                if attachment.get('type') != 'subtitle':
                    continue

                key = (attachment.get('id'), attachment.get('url'))
                if key in seen:
                    continue

                seen.add(key)
                yield attachment

        yield from collect(torrent_data.get('attachments'))

        for file in torrent_data.get('files') or []:
            yield from collect(file.get('attachments'))

    def _get_series_entries(self, episode_id):
        api_url = 'https://feed.animetosho.xyz/feed/json'

        r = self.checked(
            lambda: self.session.get(
                api_url,
                params={
                    'eid': episode_id,
                },
                timeout=10
            )
        )

        j = r.json()
        entries = list(filter(lambda t: t['status'] == 'complete', j))
        entries.sort(key=lambda t: t['timestamp'], reverse=True)
        return entries
