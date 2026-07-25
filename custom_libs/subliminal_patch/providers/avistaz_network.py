import hashlib
import io
import logging
import math
import re
import time
from pathlib import Path
from http.cookies import SimpleCookie
from random import randint

import pycountry
from requests.cookies import RequestsCookieJar
from subliminal.video import Episode
from subliminal.exceptions import AuthenticationError, ProviderError
from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.pitcher import store_verification
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language
from .utils import get_archive_from_bytes, get_subtitle_from_archive, FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)

# ── Archive cache ──────────────────────────────────────────────────────────────
# Extracted subtitle files are cached here so a full-season zip/rar is only
# downloaded once — every subsequent episode just reads from disk.
_CACHE_DIR = Path("/tmp/avistaz_sub_cache")
_SUB_EXTS  = {'.srt', '.ass', '.ssa', '.vtt'}
_SXXEXX    = re.compile(r"[Ss](\d{1,2})[Ee](\d{1,3})")
_EXX       = re.compile(r"\.E(\d{1,3})\.")
# ───────────────────────────────────────────────────────────────────────────────

supported_languages_names = [
    "Abkhazian",
    "Afar",
    "Afrikaans",
    "Akan",
    "Albanian",
    "Amharic",
    "Arabic",
    "Aragonese",
    "Armenian",
    "Assamese",
    "Avaric",
    "Avestan",
    "Aymara",
    "Azerbaijani",
    "Bambara",
    "Bashkir",
    "Basque",
    "Belarusian",
    "Bengali",
    "Bihari languages",
    "Bislama",
    "Bokmål, Norwegian",
    "Bosnian",
    "Brazilian Portuguese",
    "Breton",
    "Bulgarian",
    "Burmese",
    "Cantonese",
    "Catalan",
    "Central Khmer",
    "Chamorro",
    "Chechen",
    "Chichewa",
    "Chinese",
    "Church Slavic",
    "Chuvash",
    "Cornish",
    "Corsican",
    "Cree",
    "Croatian",
    "Czech",
    "Danish",
    "Dhivehi",
    "Dutch",
    "Dzongkha",
    "English",
    "Esperanto",
    "Estonian",
    "Ewe",
    "Faroese",
    "Fijian",
    "Filipino",
    "Finnish",
    "French",
    "Fulah",
    "Gaelic",
    "Galician",
    "Ganda",
    "Georgian",
    "German",
    "Greek",
    "Guarani",
    "Gujarati",
    "Haitian",
    "Hausa",
    "Hebrew",
    "Herero",
    "Hindi",
    "Hiri Motu",
    "Hungarian",
    "Icelandic",
    "Ido",
    "Igbo",
    "Indonesian",
    "Interlingua",
    "Interlingue",
    "Inuktitut",
    "Inupiaq",
    "Irish",
    "Italian",
    "Japanese",
    "Javanese",
    "Kalaallisut",
    "Kannada",
    "Kanuri",
    "Kashmiri",
    "Kazakh",
    "Kikuyu",
    "Kinyarwanda",
    "Kirghiz",
    "Komi",
    "Kongo",
    "Korean",
    "Kuanyama",
    "Kurdish",
    "Lao",
    "Latin",
    "Latvian",
    "Limburgan",
    "Lingala",
    "Lithuanian",
    "Luba-Katanga",
    "Luxembourgish",
    "Macedonian",
    "Malagasy",
    "Malay",
    "Malayalam",
    "Maltese",
    "Mandarin",
    "Manx",
    "Maori",
    "Marathi",
    "Marshallese",
    "Mongolian",
    "Moore",
    "Nauru",
    "Navajo",
    "Ndebele, North",
    "Ndebele, South",
    "Ndonga",
    "Nepali",
    "Northern Sami",
    "Norwegian",
    "Norwegian Nynorsk",
    "Occitan (post 1500)",
    "Ojibwa",
    "Oriya",
    "Oromo",
    "Ossetian",
    "Pali",
    "Panjabi",
    "Persian",
    "Polish",
    "Portuguese",
    "Pushto",
    "Quechua",
    "Romanian",
    "Romansh",
    "Rundi",
    "Russian",
    "Samoan",
    "Sango",
    "Sanskrit",
    "Sardinian",
    "Serbian",
    "Shona",
    "Sichuan Yi",
    "Sindhi",
    "Sinhala",
    "Slovak",
    "Slovenian",
    "Somali",
    "Sotho, Southern",
    "Spanish",
    "Sundanese",
    "Swahili",
    "Swati",
    "Swedish",
    "Tagalog",
    "Tahitian",
    "Tajik",
    "Tamil",
    "Tatar",
    "Telugu",
    "Thai",
    "Tibetan",
    "Tigrinya",
    "Tongan",
    "Tsonga",
    "Tswana",
    "Turkish",
    "Turkmen",
    "Twi",
    "Uighur",
    "Ukrainian",
    "Urdu",
    "Uzbek",
    "Venda",
    "Vietnamese",
    "Volapük",
    "Walloon",
    "Welsh",
    "Western Frisian",
    "Wolof",
    "Xhosa",
    "Yiddish",
    "Yoruba",
    "Zhuang",
    "Zulu"
]


class AvistazNetworkSubtitle(Subtitle):
    """AvistaZ.to Subtitle."""
    provider_name = None

    def __init__(self, provider_name, page_link, download_link, language, video, filename, release, uploader,
                 downloads=0, likes=0, dislikes=0):
        super().__init__(language, page_link=page_link)
        self.provider_name = provider_name
        self.hearing_impaired = None
        self.filename = filename
        self.release_info = release
        self.page_link = page_link
        self.download_link = download_link
        self.video = video
        self.matches = set()
        self.content = None
        self.uploader = uploader
        self.downloads = downloads
        self.likes = likes
        self.dislikes = dislikes
        self.encoding = None

    @property
    def id(self):
        return self.filename

    def get_matches(self, video):
        # we download subtitles directly from the
        # release page, so it's always a perfect match
        self.matches = {'hash'}
        return self.matches


def lookup_lang(name):
    try:
        return Language(pycountry.languages.lookup(name).alpha_3)
    except:
        return None


class AvistazNetworkProviderBase(Provider):
    """AvistaZ Network base provider"""
    subtitle_class = AvistazNetworkSubtitle
    languages = set(filter(None, map(lookup_lang, supported_languages_names)))
    languages.update(set(Language.rebuild(L, hi=True) for L in languages))

    server_url = None
    provider_name = None
    hash_verifiable = True

    def __init__(self, cookies, user_agent=None):
        self.session = None
        self.cookies = cookies
        self.user_agent = user_agent

    def initialize(self):
        self.session = RetryingCFSession()

        if self.user_agent:
            self.session.headers['User-Agent'] = self.user_agent
        else:
            self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

        if self.cookies:
            self.session.cookies = RequestsCookieJar()
            simple_cookie = SimpleCookie()
            simple_cookie.load(self.cookies)

            for k, v in simple_cookie.items():
                self.session.cookies.set(k, v.value)

            rr = self.session.get(self.server_url + 'rules', allow_redirects=False, timeout=10,
                                  headers={"Referer": self.server_url})
            if rr.status_code in [302, 404, 403]:
                logger.info('Cookies expired')
                raise AuthenticationError("cookies not valid anymore")

            store_verification(self.provider_name, self.session)
            logger.debug('Cookies valid')
            time.sleep(2)
            return True

    def terminate(self):
        self.session.close()

    def list_subtitles(self, video, languages):
        if video.info_url is None or not video.info_url.startswith(self.server_url):
            logger.debug('%s not downloaded from %s. Skipped', video, self.server_url)
            return []

        html = self._query_info_url(video.info_url)

        if html is None:
            logger.debug('%s release page not found. Release might have been removed', video)
            return []

        release = self._parse_release_table(html)

        if release['Subtitles'].table is None:
            logger.debug('No subtitles found for %s', video)
            return []

        subtitle_columns = list(map(lambda x: x.get_text(), release['Subtitles'].thead.find_all('th')))

        subtitles = []
        for row in release['Subtitles'].tbody.find_all('tr', recursive=False):

            subtitle_cols = self._parse_subtitle_row(row, subtitle_columns)

            release_name  = release['Title'].get_text().strip()
            lang          = lookup_lang(subtitle_cols['Language'].get_text().strip())
            download_link = subtitle_cols['Download'].a['href']
            uploader_name = subtitle_cols['Uploader'].get_text().strip() if 'Uploader' in subtitle_cols else None

            # Download count
            try:
                downloads = int(subtitle_cols['Downloads'].get_text().strip().replace(',', ''))
            except (KeyError, ValueError):
                downloads = 0

            # Likes / dislikes from the unnamed rating column
            likes, dislikes = 0, 0
            for key, cell in subtitle_cols.items():
                if key == '' and cell.find(class_='subtitle-likes'):
                    try:
                        likes    = int(cell.select_one('a[data-like="like"] .count').get_text().strip())
                        dislikes = int(cell.select_one('a[data-like="dislike"] .count').get_text().strip())
                    except (AttributeError, ValueError):
                        pass
                    break

            if lang not in languages:
                continue

            # Build a descriptive release_info so each subtitle appears as a
            # distinct, informative result in Bazarr's manual search UI
            ext          = "ZIP" if download_link.endswith(".zip")                            else "RAR" if download_link.endswith(".rar")                            else "SRT"
            rating_str   = f"{likes}\U0001f44d {dislikes}\U0001f44e" if (likes or dislikes) else f"{downloads}\u2193"
            uploader_str = uploader_name if uploader_name else "unknown"
            display_release = f"{release_name} [{uploader_str}] {ext} {rating_str}"

            subtitles.append(self.subtitle_class(
                provider_name=self.provider_name,
                page_link=video.info_url,
                download_link=download_link,
                language=lang,
                video=video,
                filename=download_link.split('/')[-1],
                release=display_release,
                uploader=uploader_name,
                downloads=downloads,
                likes=likes,
                dislikes=dislikes,
            ))

        # Sort by:
        #   1. Full-season archives (zip/rar) before single-episode srt files
        #   2. Net rating (likes - dislikes) descending
        #   3. Download count descending as tiebreaker
        subtitles.sort(key=lambda s: (
            0 if s.filename.endswith((".zip", ".rar")) else 1,
            -(s.likes - s.dislikes),
            -s.downloads,
        ))

        return subtitles

    def _query_info_url(self, info_url):
        response = self.session.get(info_url, timeout=30)

        if response.status_code == 404:
            return None
        else:
            response.raise_for_status()

        return response.content.decode('utf-8', 'ignore')

    def _parse_subtitle_row(self, row, subtitle_columns):
        columns = {}
        for i, data in enumerate(row.find_all('td', recursive=False)):
            columns[subtitle_columns[i]] = data
        return columns

    def _parse_release_table(self, html):
        release_data_table = (ParserBeautifulSoup(html, ['html.parser'])
                              .select_one('#content-area > div.block > div.table-responsive > table > tbody'))

        if release_data_table is None:
            raise ProviderError('Unexpected HTML page layout - no release data table found')

        rows = {}
        for tr in release_data_table.find_all('tr', recursive=False):
            rows[tr.td.get_text()] = tr.select_one('td:nth-child(2)', recursive=False)
        return rows

    def _cache_dir_for(self, download_link):
        """Return a unique cache directory path for this download URL."""
        key = hashlib.md5(download_link.encode()).hexdigest()
        return _CACHE_DIR / key

    def _extract_to_cache(self, data, cache_dir):
        """Extract every subtitle file from a zip or rar into cache_dir."""
        import zipfile
        cache_dir.mkdir(parents=True, exist_ok=True)

        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in zf.namelist():
                    if Path(name).suffix.lower() in _SUB_EXTS:
                        (cache_dir / Path(name).name).write_bytes(zf.read(name))
            return

        try:
            import rarfile
            with rarfile.RarFile(io.BytesIO(data)) as rf:
                for entry in rf.infolist():
                    if Path(entry.filename).suffix.lower() in _SUB_EXTS:
                        (cache_dir / Path(entry.filename).name).write_bytes(rf.read(entry))
        except Exception as e:
            logger.debug('Failed to extract rar to cache: %s', e)

    def _read_sonarr_config(self):
        """Read Sonarr URL and API key from Bazarr config."""
        try:
            from app.config import get_settings
            s      = get_settings()
            sonarr = s.sonarr
            scheme = 'https' if getattr(sonarr, 'ssl', False) else 'http'
            ip     = getattr(sonarr, 'ip', '127.0.0.1')
            port   = getattr(sonarr, 'port', 8989)
            base   = getattr(sonarr, 'base_url', '').strip('/')
            apikey = getattr(sonarr, 'apikey', '')
            url    = '{}://{}:{}/{}'.format(scheme, ip, port, base) if base                      else '{}://{}:{}'.format(scheme, ip, port)
            return url, apikey
        except Exception:
            pass

        try:
            import os
            import yaml
            candidates = [
                '/opt/bazarr/data/config/config.yaml',
                '/config/config/config.yaml',
            ]
            for path in candidates:
                if not os.path.exists(path):
                    continue
                with open(path) as f:
                    config = yaml.safe_load(f)
                sonarr = config.get('sonarr', {})
                scheme = 'https' if sonarr.get('ssl', False) else 'http'
                ip     = sonarr.get('ip', '127.0.0.1')
                port   = sonarr.get('port', 8989)
                base   = sonarr.get('base_url', '').strip('/')
                apikey = sonarr.get('apikey', '')
                url    = '{}://{}:{}/{}'.format(scheme, ip, port, base) if base                          else '{}://{}:{}'.format(scheme, ip, port)
                return url, apikey
        except Exception as e:
            logger.debug('Failed to read Sonarr config: %s', e)

        return None, None

    def _get_season_episode_count(self, sonarr_episode_id):
        """
        Query Sonarr for the total number of episodes in the same season as
        the given episode ID. Used to detect ratio mismatches between subtitle
        file count and episode count (e.g. 16 subtitle files for 32 episodes).
        Returns the count as an int, or None if the query fails.
        """
        try:
            import requests as req
            sonarr_url, sonarr_api_key = self._read_sonarr_config()
            if not sonarr_url or not sonarr_api_key:
                return None

            headers = {'X-Api-Key': sonarr_api_key}

            # Get episode details to find series ID and season number
            ep_resp = req.get(
                sonarr_url.rstrip('/') + '/api/v3/episode/{}'.format(sonarr_episode_id),
                headers=headers,
                timeout=10,
            )
            ep_resp.raise_for_status()
            ep_data   = ep_resp.json()
            series_id = ep_data.get('seriesId')
            season_num = ep_data.get('seasonNumber')

            if not series_id or season_num is None:
                return None

            # Count all episodes in this season
            eps_resp = req.get(
                sonarr_url.rstrip('/') + '/api/v3/episode',
                headers=headers,
                params={'seriesId': series_id, 'seasonNumber': season_num},
                timeout=10,
            )
            eps_resp.raise_for_status()
            count = len(eps_resp.json())
            logger.debug('Sonarr season episode count for episode %s: %d', sonarr_episode_id, count)
            return count

        except Exception as e:
            logger.debug('Failed to get season episode count from Sonarr: %s', e)
            return None

    def _pick_from_cache(self, cache_dir, episode_num, sonarr_episode_id=None):
        """
        Find the subtitle in cache_dir matching episode_num.

        When sonarr_episode_id is provided, queries Sonarr for total season
        episode count to detect ratio mismatches (e.g. 16 subtitle files for
        a 32-episode season). In that case ratio mapping is used instead of
        exact filename matching so that episode 5 correctly maps to subtitle 3
        rather than subtitle 5.

        Falls back to exact SxxExx / Exx filename matching when no mismatch
        is detected or when the Sonarr query fails.
        """
        sub_files = sorted(
            [f for f in cache_dir.iterdir() if f.suffix.lower() in _SUB_EXTS]
        )
        num_subs = len(sub_files)

        if not sub_files:
            return None

        # Check if ratio mapping is needed by comparing subtitle count
        # to total episode count from Sonarr
        if sonarr_episode_id:
            total_episodes = self._get_season_episode_count(sonarr_episode_id)
            if total_episodes and total_episodes > num_subs:
                ratio   = total_episodes / num_subs
                sub_idx = min(math.ceil(episode_num / ratio) - 1, num_subs - 1)
                sub_idx = max(0, sub_idx)
                mapped_f = sub_files[sub_idx]
                logger.debug(
                    'Ratio mapping: %d eps / %d subs = %.1f, ep%d → %s',
                    total_episodes, num_subs, ratio, episode_num, mapped_f.name,
                )
                return mapped_f.read_bytes()

        # Exact match — SxxExx style e.g. S01E07
        for f in sub_files:
            m = _SXXEXX.search(f.name)
            if m and int(m.group(2)) == episode_num:
                return f.read_bytes()

        # Exact match — season-less Exx style e.g. .E07.
        for f in sub_files:
            m = _EXX.search(f.name)
            if m and int(m.group(1)) == episode_num:
                return f.read_bytes()

        return None

    def download_subtitle(self, subtitle):
        if subtitle.filename.endswith((".zip", ".rar")):
            episode_num = subtitle.video.episode if isinstance(subtitle.video, Episode) else None
            cache_dir   = self._cache_dir_for(subtitle.download_link)

            # Download and extract only if not already cached
            if not cache_dir.exists() or not any(cache_dir.iterdir()):
                response = self.session.get(subtitle.download_link)
                response.raise_for_status()
                self._extract_to_cache(response.content, cache_dir)

            # Pick the right episode subtitle from cache
            if episode_num is not None:
                sonarr_episode_id = getattr(subtitle.video, 'sonarrEpisodeId', None)
                content = self._pick_from_cache(cache_dir, episode_num, sonarr_episode_id=sonarr_episode_id)
                if content:
                    subtitle.content = content
                    return

            # Fallback to original single-file extraction
            response = self.session.get(subtitle.download_link)
            response.raise_for_status()
            archive = get_archive_from_bytes(response.content)
            subtitle.content = get_subtitle_from_archive(archive, episode=episode_num)

        else:
            # Single file — cache raw bytes to avoid re-downloading per episode
            cache_dir   = self._cache_dir_for(subtitle.download_link)
            cached_file = cache_dir / subtitle.filename
            if cached_file.exists():
                subtitle.content = cached_file.read_bytes()
            else:
                response = self.session.get(subtitle.download_link)
                response.raise_for_status()
                cache_dir.mkdir(parents=True, exist_ok=True)
                cached_file.write_bytes(response.content)
                subtitle.content = response.content
