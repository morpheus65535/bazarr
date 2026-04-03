# -*- coding: utf-8 -*-
import logging
import os
import time
import io

from zipfile import ZipFile, is_zipfile
from urllib.parse import urljoin
from requests import Session
from guessit import guessit

from babelfish import language_converters
from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.exceptions import ConfigurationError, ProviderError, DownloadLimitExceeded
from subliminal_patch.exceptions import APIThrottled
from .mixins import ProviderRetryMixin
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils

logger = logging.getLogger(__name__)

retry_amount = 3
retry_timeout = 5

language_converters.register('subdl = subliminal_patch.converters.subdl:SubdlConverter')


class SubdlSubtitle(Subtitle):
    provider_name = 'subdl'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, download_link, file_id, release_names, uploader,
                 season=None, episode=None, absolute_episode=None, is_pack=False):
        super().__init__(language)
        language = Language.rebuild(language, hi=hearing_impaired, forced=forced)

        self.season = season
        self.episode = episode
        self.absolute_episode = absolute_episode
        self.is_pack = is_pack
        self.releases = release_names
        self.release_info = ', '.join(release_names)
        self.language = language
        self.forced = forced
        self.hearing_impaired = hearing_impaired
        self.file_id = file_id
        self.page_link = page_link
        self.download_link = download_link
        self.uploader = uploader
        self.matches = set()

    @property
    def id(self):
        return self.file_id

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # season
            if video.season == self.season:
                matches.add('season')
            elif self.is_pack and self.absolute_episode:
                # Arc-based season numbering (e.g. subdl's Enies Lobby = S09) differs from
                # Sonarr's sequential numbering (S11). When a pack is validated via absolute
                # episode range, trust the match regardless of season number discrepancy.
                matches.add('season')
            # episode — match by standard episode, absolute episode, or pack range
            if video.episode == self.episode:
                matches.add('episode')
            elif (getattr(video, 'absolute_episode', None) and
                  video.absolute_episode == self.episode):
                matches.add('episode')
            elif self.is_pack:
                # Pack was already validated to contain the target episode
                matches.add('episode')
            # imdb — IMDB match also confirms the year
            matches.add('series_imdb_id')
            if video.year:
                matches.add('year')
        else:
            # title
            matches.add('title')
            # imdb
            matches.add('imdb_id')
            # tmdb 
            matches.add('tmdb_id')

        utils.update_matches(matches, video, self.releases)

        self.matches = matches

        return matches


class SubdlProvider(ProviderRetryMixin, Provider):
    """Subdl Provider"""
    server_hostname = 'api.subdl.com'

    languages = {Language(*lang) for lang in list(language_converters['subdl'].to_subdl.keys())}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    languages.update(set(Language.rebuild(l, hi=True) for l in languages))

    video_types = (Episode, Movie)

    def __init__(self, api_key=None):
        if not api_key:
            raise ConfigurationError('Api_key must be specified')

        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        self.api_key = api_key
        self.video = None
        self._started = None

    def initialize(self):
        self._started = time.time()

    def terminate(self):
        self.session.close()

    def server_url(self):
        return f'https://{self.server_hostname}/api/v1/'

    def query(self, languages, video):
        self.video = video
        if isinstance(self.video, Episode):
            title = self.video.series
        else:
            title = self.video.title

        imdb_id = None
        tmdb_id = None
        if isinstance(self.video, Episode) and self.video.series_imdb_id:
            imdb_id = self.video.series_imdb_id
        elif isinstance(self.video, Movie):
            if self.video.imdb_id:
               imdb_id = self.video.imdb_id
            if self.video.tmdb_id:
               tmdb_id = self.video.tmdb_id

        # be sure to remove duplicates using list(set())
        langs_list = sorted(list(set([language_converters['subdl'].convert(lang.alpha3, lang.country, lang.script) for
                                      lang in languages])))

        langs = ','.join(langs_list)
        logger.debug(f'Searching for those languages: {langs}')

        # query the server
        if isinstance(self.video, Episode):
            res = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=(('api_key', self.api_key),
                                                 ('episode_number', self.video.episode),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('languages', langs),
                                                 ('season_number', self.video.season),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('comment', 1),
                                                 ('releases', 1),
                                                 ('bazarr', 1)),  # this argument filter incompatible image based or
                                         # txt subtitles
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )

            # For anime with absolute episode numbering, also search by absolute episode number
            # so we can find subtitles that are only indexed by absolute number on subdl
            absolute_episode = getattr(self.video, 'absolute_episode', None)
            if absolute_episode and absolute_episode != self.video.episode:
                logger.debug(f'Also searching by absolute episode number: {absolute_episode}')
                res_absolute = self.retry(
                    lambda: self.session.get(self.server_url() + 'subtitles',
                                             params=(('api_key', self.api_key),
                                                     ('episode_number', absolute_episode),
                                                     ('film_name', title if not imdb_id else None),
                                                     ('imdb_id', imdb_id if imdb_id else None),
                                                     ('languages', langs),
                                                     ('subs_per_page', 30),
                                                     ('type', 'tv'),
                                                     ('comment', 1),
                                                     ('releases', 1),
                                                     ('bazarr', 1)),
                                             timeout=30),
                    amount=retry_amount,
                    retry_timeout=retry_timeout
                )
            else:
                res_absolute = None

            # Fallback: search by season only (no episode filter) to catch subtitles that use
            # split-season / cour-based internal numbering (e.g. Fire Force S3 split into two cours
            # where episode 25 is stored internally as cour-2 episode 13).
            # The release name matching in get_matches() will identify the correct episode.
            logger.debug(f'Also searching by season only (no episode filter) for season {self.video.season}')
            res_season = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=(('api_key', self.api_key),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('languages', langs),
                                                 ('season_number', self.video.season),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('comment', 1),
                                                 ('releases', 1),
                                                 ('bazarr', 1)),
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )
        else:
            res_absolute = None
            res_season = None
            params = {
                       'api_key': self.api_key,
                       'film_name': title if not imdb_id else None,
                       'imdb_id': imdb_id,
                       'languages': langs,
                       'subs_per_page': 30,
                       'type': 'movie',
                       'comment': 1,
                       'releases': 1,
                       'bazarr': 1
            }
            res = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=params, # this argument filter incompatible image based or
                                         # txt subtitles
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )

            # subdl also allows searching by TMDB ID, and some movies don't always
            # have the correct IMDB ID, or may not have it at all. We also search by TMDB ID
            # if it's available for the movie.
            if res.status_code == 200:
                # if the previous request with IMDb ID reported errors
                res_data=res.json()

                if 'status' in res_data and not res_data['status']:
                    if not tmdb_id:
                        logger.debug("No subtitles found via IMDb id or film name. TMDB ID unavailable for fallback")

                    # If the movie also has the TMDB ID code, we try to search
                    # for subtitles using only the TMDB ID code
                    else:
                        logger.debug("No subtitles found via IMDb id or film name. Search instead with TMDB id")

                        params.pop('film_name', None)
                        params.pop('imdb_id', None)
                        params['tmdb_id']=tmdb_id

                        res = self.retry(
                            lambda: self.session.get(self.server_url() + 'subtitles',
                                                     params=params,
                                                     timeout=30),
                            amount=retry_amount,
                            retry_timeout=retry_timeout
                        )

        if res.status_code == 429:
            raise APIThrottled("Too many requests")
        elif res.status_code == 403:
            raise ConfigurationError("Invalid API key")
        elif res.status_code != 200:
            res.raise_for_status()

        subtitles = []

        result = res.json()

        if ('success' in result and not result['success']) or ('status' in result and not result['status']):
            logger.debug(result)
            if 'error' in result:
                error_msg = result['error']
                if "can't find" in error_msg.lower():
                    logger.debug(f"No subtitles found for {imdb_id or title}: {error_msg}")
                    return subtitles
                raise ProviderError(error_msg)

        # Merge absolute episode search results if available
        all_items = list(result.get('subtitles', []))
        seen_ids = {item['name'] for item in all_items}

        if res_absolute and res_absolute.status_code == 200:
            abs_result = res_absolute.json()
            if ('success' in abs_result and abs_result['success']) or ('status' in abs_result and abs_result['status']):
                for item in abs_result.get('subtitles', []):
                    if item['name'] not in seen_ids:
                        all_items.append(item)
                        seen_ids.add(item['name'])
                logger.debug(f'Absolute episode search added {len(abs_result.get("subtitles", []))} more subtitles')

        if res_season and res_season.status_code == 200:
            season_result = res_season.json()
            if ('success' in season_result and season_result['success']) or ('status' in season_result and season_result['status']):
                added = 0
                for item in season_result.get('subtitles', []):
                    if item['name'] not in seen_ids:
                        all_items.append(item)
                        seen_ids.add(item['name'])
                        added += 1
                logger.debug(f'Season-only search added {added} more subtitles')

        # Last resort: if all season-filtered searches returned nothing, search by title only
        # (no season/episode filter). This catches anime stored as season 0 on subdl (full series
        # blocks) where season_number filtering silently excludes all results.
        if not all_items and isinstance(self.video, Episode):
            logger.debug('All season-filtered searches returned 0 results, falling back to title-only search')
            res_title = self.retry(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=(('api_key', self.api_key),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('languages', langs),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('comment', 1),
                                                 ('releases', 1),
                                                 ('bazarr', 1)),
                                         timeout=30),
                amount=retry_amount,
                retry_timeout=retry_timeout
            )
            if res_title.status_code == 200:
                title_result = res_title.json()
                if ('success' in title_result and title_result['success']) or \
                        ('status' in title_result and title_result['status']):
                    added = 0
                    for item in title_result.get('subtitles', []):
                        if item['name'] not in seen_ids:
                            all_items.append(item)
                            seen_ids.add(item['name'])
                            added += 1
                    logger.debug(f'Title-only fallback search added {added} subtitles')

        logger.debug(f"Query returned {len(all_items)} subtitles")

        absolute_episode = getattr(self.video, 'absolute_episode', None)

        if len(all_items):
            for item in all_items:
                is_pack = False
                if isinstance(self.video, Episode):
                    ep_from = item.get('episode_from')
                    ep_end = item.get('episode_end')
                    # Fallback: parse episode range from release names when the API
                    # does not provide episode_from/episode_end fields.
                    if not (ep_from and ep_end and ep_from != ep_end):
                        ep_from_parsed, ep_end_parsed = self._parse_episode_range_from_releases(
                            item.get('releases', [])
                        )
                        if ep_from_parsed and ep_end_parsed and ep_from_parsed != ep_end_parsed:
                            ep_from = ep_from_parsed
                            ep_end = ep_end_parsed
                            logger.debug(
                                f'Parsed episode range {ep_from}-{ep_end} from release names'
                            )
                    if ep_from and ep_end and ep_from != ep_end:
                        # Multi-episode pack: allow if target episode is within range
                        target_ep = self.video.episode
                        if absolute_episode:
                            # Check both standard and absolute episode against the range
                            if not ((ep_from <= target_ep <= ep_end) or
                                    (ep_from <= absolute_episode <= ep_end)):
                                continue
                        else:
                            if not (ep_from <= target_ep <= ep_end):
                                continue
                        is_pack = True

                subtitle = SubdlSubtitle(
                    language=Language.fromsubdl(item['language']),
                    forced=self._is_forced(item),
                    hearing_impaired=item.get('hi', False) or self._is_hi(item),
                    page_link=urljoin("https://subdl.com", item.get('subtitlePage', '')),
                    download_link=item['url'],
                    file_id=item['name'],
                    release_names=item.get('releases', []),
                    uploader=item.get('author', ''),
                    season=item.get('season', None),
                    episode=item.get('episode', None),
                    absolute_episode=absolute_episode,
                    is_pack=is_pack,
                )
                subtitle.get_matches(self.video)
                if subtitle.language in languages:  # make sure only desired subtitles variants are returned
                    subtitles.append(subtitle)

        return subtitles

    @staticmethod
    def _is_hi(item):
        # Comments include specific mention of removed or non HI
        non_hi_tag = ['hi remove', 'non hi', 'nonhi', 'non-hi', 'non-sdh', 'non sdh', 'nonsdh', 'sdh remove']
        for tag in non_hi_tag:
            if tag in item.get('comment', '').lower():
                return False

        # Archive filename include _HI_
        if '_hi_' in item.get('name', '').lower():
            return True

        # Comments or release names include some specific strings
        hi_keys = [item.get('comment', '').lower(), [x.lower() for x in item.get('releases', [])]]
        hi_tag = ['_hi_', ' hi ', '.hi.', 'hi ', ' hi', 'sdh', '𝓢𝓓𝓗']
        for key in hi_keys:
            if any(x in key for x in hi_tag):
                return True

        # nothing match so we consider it as non-HI
        return False

    @staticmethod
    def _is_forced(item):
        # Comments include specific mention of forced subtitles
        forced_tags = ['forced', 'foreign']
        for tag in forced_tags:
            if tag in item.get('comment', '').lower():
                return True

        # nothing match so we consider it as normal subtitles
        return False

    @staticmethod
    def _parse_episode_range_from_releases(release_names):
        """Parse episode range (ep_from, ep_end) from release name strings.

        Used as a fallback when the subdl API does not populate episode_from/
        episode_end for a pack. Guessit expands patterns like 'EP0264-0336'
        into a list of integers; we extract the first and last as the range.

        Returns (ep_from, ep_end) as ints, or (None, None) if not found.
        """
        for name in release_names:
            guess = guessit(name, {'type': 'episode'})
            ep = guess.get('episode')
            if isinstance(ep, list) and len(ep) >= 2:
                return ep[0], ep[-1]
        return None, None

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.debug('Downloading subtitle %r', subtitle)
        download_link = urljoin("https://dl.subdl.com", subtitle.download_link)

        r = self.retry(
            lambda: self.session.get(download_link, timeout=30),
            amount=retry_amount,
            retry_timeout=retry_timeout
        )

        if r.status_code == 429 or (r.status_code == 500 and r.text == 'Download limit exceeded'):
            raise DownloadLimitExceeded("Daily download limit exceeded")
        elif r.status_code == 403:
            raise ConfigurationError("Invalid API key")
        elif r.status_code != 200:
            r.raise_for_status()

        if not r:
            logger.error(f'Could not download subtitle from {download_link}')
            subtitle.content = None
            return
        else:
            archive_stream = io.BytesIO(r.content)
            if is_zipfile(archive_stream):
                archive = ZipFile(archive_stream)
                if subtitle.is_pack and self.video and isinstance(self.video, Episode):
                    # Use smart extraction for packs: match by episode number
                    target_episode = self.video.episode
                    absolute_episode = getattr(self.video, 'absolute_episode', None)
                    content = utils.get_subtitle_from_archive(
                        archive,
                        episode=target_episode,
                        episode_title=getattr(self.video, 'title', None),
                    )
                    # Fallback: try absolute episode number
                    if content is None and absolute_episode:
                        content = utils.get_subtitle_from_archive(
                            archive,
                            episode=absolute_episode,
                        )
                    if content is not None:
                        subtitle.content = content
                    else:
                        logger.warning(f'Could not find episode {target_episode} in pack archive {download_link}')
                        subtitle.content = None
                else:
                    # Single episode: prefer subtitle file extensions, fallback to first file
                    for name in archive.namelist():
                        if name.endswith(('.srt', '.sub', '.ssa', '.ass')):
                            subtitle.content = fix_line_ending(archive.read(name))
                            return
                    for name in archive.namelist():
                        subtitle.content = fix_line_ending(archive.read(name))
                        return
            else:
                logger.error(f'Could not unzip subtitle from {download_link}')
                subtitle.content = None
                return
