# -*- coding: utf-8 -*-
import logging
import lzma
import os
import re
from difflib import SequenceMatcher
from urllib.parse import quote

from babelfish import language_converters
from guessit import guessit
from requests import Session
from requests.exceptions import RequestException
from subzero.language import Language

from subliminal.exceptions import ProviderError
from subliminal.video import Episode, Movie
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches

logger = logging.getLogger(__name__)

API_URL = 'https://api.tsukihime.org/v1'
STORAGE_URL = 'https://storage.tsukihime.org'
MAX_TORRENTS = 20


def _language_from_code(code):
    if not code:
        return None

    normalized = code.strip().lower()
    aliases = {
        'es-419': Language('spa', 'MX'),
        'es-es': Language('spa'),
        'pt-br': Language('por', 'BR'),
        'pt-pt': Language('por'),
        'zh-cn': Language('zho', 'CN'),
        'zh-hans': Language('zho', 'CN'),
        'zh-hant': Language('zho', 'TW'),
        'zh-tw': Language('zho', 'TW'),
    }
    if normalized in aliases:
        return aliases[normalized]

    try:
        if len(normalized) == 2:
            return Language.fromalpha2(normalized)
        return Language.fromietf(normalized)
    except (KeyError, ValueError):
        try:
            return Language.fromalpha3b(normalized)
        except (KeyError, ValueError):
            logger.debug('Unsupported TsukiHime language code: %s', code)
            return None


SUPPORTED_LANGUAGES = {Language.fromalpha2(code) for code in language_converters['alpha2'].codes} | {
    Language('spa', 'MX'), Language('por', 'BR'), Language('zho', 'CN'), Language('zho', 'TW'),
}


class TsukiHimeSubtitle(Subtitle):
    """Subtitle extracted from a release indexed by TsukiHime."""

    provider_name = 'tsukihime'

    def __init__(self, language, download_url, release_info, filename, codec, verified_matches,
                 hearing_impaired=False):
        super(TsukiHimeSubtitle, self).__init__(
            language,
            hearing_impaired=hearing_impaired,
            page_link=download_url,
            original_format=True,
        )
        self.download_url = download_url
        self.release_info = release_info
        self.filename = filename
        self.format = codec.lower()
        self.verified_matches = verified_matches

    @property
    def id(self):
        return self.download_url

    def get_matches(self, video):
        video_type = 'episode' if isinstance(video, Episode) else 'movie'
        self.matches |= guess_matches(video, guessit(self.release_info, {'type': video_type}))
        self.matches |= guess_matches(video, guessit(self.filename, {'type': video_type}))
        self.matches.update(self.verified_matches)
        return self.matches


class TsukiHimeProvider(Provider):
    """TsukiHime anime subtitle provider."""

    provider_name = 'tsukihime'
    subtitle_class = TsukiHimeSubtitle
    languages = SUPPORTED_LANGUAGES
    video_types = (Episode, Movie)

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers.update({'User-Agent': os.environ.get('SZ_USER_AGENT', 'Bazarr')})

    def terminate(self):
        self.session.close()

    def list_subtitles(self, video, languages):
        anime = self._get_anime(video)
        if not anime:
            return []

        requested_languages = set(languages)
        entries = [
            entry for entry in self._get_entries(video, anime['id'])
            if entry.get('state') == 'completed'
            and self._has_requested_language(entry.get('sublangs', []), requested_languages)
        ]
        entries.sort(key=lambda entry: self._entry_score(video, entry), reverse=True)

        subtitles = []
        seen_urls = set()
        for entry in entries[:MAX_TORRENTS]:
            entry_id = entry.get('id')
            if entry_id is None:
                continue

            detail = self._get_json(f'/torrents/{entry_id}')
            if not detail:
                continue

            for file_data in self._matching_files(video, detail.get('files', [])):
                for attachment in file_data.get('attachments', []):
                    subtitle = self._subtitle_from_attachment(
                        video,
                        anime,
                        entry,
                        file_data,
                        attachment,
                        requested_languages,
                    )
                    if subtitle and subtitle.download_url not in seen_urls:
                        seen_urls.add(subtitle.download_url)
                        subtitles.append(subtitle)

        return subtitles

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)
        response = self._request(subtitle.download_url)
        if not response.content.startswith(b'\xFD\x37\x7A\x58\x5A\x00'):
            raise ProviderError('TsukiHime returned an unidentified archive type')

        try:
            subtitle.content = lzma.decompress(response.content)
        except lzma.LZMAError as error:
            raise ProviderError('TsukiHime subtitle decompression failed') from error
        return subtitle

    def _get_anime(self, video):
        if isinstance(video, Episode):
            anidb_id = self._scalar(getattr(video, 'series_anidb_id', None))
            if not anidb_id:
                logger.debug('Skipping %r because no AniDB series ID was identified', video)
                return None
            return self._get_json(f'/animes/anidb/{anidb_id}')

        anilist_id = self._scalar(getattr(video, 'anilist_id', None))
        if not anilist_id:
            logger.debug('Skipping %r because no AniList movie ID was identified', video)
            return None
        return self._get_json(f'/animes/anilist/{anilist_id}')

    def _get_entries(self, video, anime_id):
        if isinstance(video, Episode):
            episode = self._scalar(getattr(video, 'series_anidb_episode_no', None)) or video.episode
            data = self._get_json(f'/animes/{anime_id}/episodes/{episode}')
        else:
            data = self._get_json(f'/animes/{anime_id}')
        return data.get('results', []) if data else []

    def _subtitle_from_attachment(self, video, anime, entry, file_data, attachment, requested_languages):
        if attachment.get('type') != 1:
            return None

        info = attachment.get('info') or {}
        if info.get('cached') == 0:
            return None

        language = _language_from_code(info.get('lang'))
        if not language:
            return None
        if info.get('forced'):
            language = Language.rebuild(language, forced=True)

        name = info.get('name', '').lower()
        hearing_impaired = bool(re.search(r'(?:^|[\s_.-])(cc|sdh|hearing[\s_.-]*impaired)(?:$|[\s_.-])', name))
        if hearing_impaired:
            language = Language.rebuild(language, hi=True)
        if language not in requested_languages:
            return None

        codec = info.get('codec', '').lower()
        track_number = info.get('tracknum')
        attachment_id = attachment.get('id')
        if codec not in ('ass', 'srt', 'ssa', 'sub', 'vtt') or track_number is None or attachment_id is None:
            return None

        media_filename = file_data.get('filename', '')
        filename_root = os.path.splitext(media_filename)[0]
        subtitle_filename = f"{filename_root}_track{track_number}.{info['lang']}.{codec}.xz"
        storage_path = 'tosho/attach' if entry.get('animetosho') else 'attach'
        download_url = (
            f'{STORAGE_URL}/{storage_path}/{int(attachment_id):08X}/'
            f'{quote(subtitle_filename, safe="")}'
        )

        verified_matches = {'title'} if isinstance(video, Movie) else {'series', 'season', 'episode'}
        if video.year and anime.get('release_year') == video.year:
            verified_matches.add('year')

        return self.subtitle_class(
            language,
            download_url,
            release_info=entry.get('name', media_filename),
            filename=media_filename,
            codec=codec,
            verified_matches=verified_matches,
            hearing_impaired=hearing_impaired,
        )

    def _get_json(self, path):
        response = self._request(f'{API_URL}{path}', allow_not_found=True)
        if response is None:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise ProviderError(f'TsukiHime returned invalid JSON for {path}') from error

    def _request(self, url, allow_not_found=False):
        try:
            response = self.session.get(url, timeout=10)
        except RequestException as error:
            logger.exception('TsukiHime request failed for %s', url)
            raise ProviderError('TsukiHime request failed; check the Bazarr log') from error

        if allow_not_found and response.status_code == 404:
            return None
        if response.status_code != 200:
            raise ProviderError(f'TsukiHime returned HTTP {response.status_code} for {url}')
        return response

    @staticmethod
    def _scalar(value):
        if isinstance(value, (list, tuple)):
            return value[-1] if value else None
        return value

    @staticmethod
    def _has_requested_language(codes, requested_languages):
        requested_alpha3 = {language.alpha3 for language in requested_languages}
        return any(
            language and language.alpha3 in requested_alpha3
            for language in (_language_from_code(code) for code in codes)
        )

    @staticmethod
    def _entry_score(video, entry):
        def normalize(value):
            return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()

        original_name = getattr(video, 'original_name', None) or video.name
        original_name = os.path.splitext(original_name)[0]
        similarity = SequenceMatcher(None, normalize(original_name), normalize(entry.get('name', ''))).ratio()
        try:
            source_date = int(entry.get('source_date', 0))
        except (TypeError, ValueError):
            source_date = 0
        return similarity, source_date

    @classmethod
    def _matching_files(cls, video, files):
        if len(files) <= 1:
            return files

        original_name = getattr(video, 'original_name', None) or video.name
        if isinstance(video, Movie):
            original_name = os.path.splitext(original_name)[0].lower()
            return [max(
                files,
                key=lambda file_data: SequenceMatcher(
                    None,
                    original_name,
                    os.path.splitext(file_data.get('filename', ''))[0].lower(),
                ).ratio(),
            )]

        expected = {
            cls._scalar(getattr(video, 'series_anidb_episode_no', None)),
            video.episode,
        }
        expected.discard(None)
        matching = []
        for file_data in files:
            guessed_episode = guessit(file_data.get('filename', ''), {'type': 'episode'}).get('episode')
            guessed_episodes = guessed_episode if isinstance(guessed_episode, (list, tuple)) else [guessed_episode]
            if expected.intersection(guessed_episodes):
                matching.append(file_data)
        return matching
