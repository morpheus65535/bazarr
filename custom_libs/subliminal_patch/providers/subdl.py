# -*- coding: utf-8 -*-
import logging
import os
import time
import io
from typing import Callable

from zipfile import ZipFile, is_zipfile
from urllib.parse import urljoin
from requests import Session, Response
from guessit import guessit

from babelfish import language_converters
from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.exceptions import ConfigurationError, ProviderError, DownloadLimitExceeded, AuthenticationError
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils

logger = logging.getLogger(__name__)

language_converters.register('subdl = subliminal_patch.converters.subdl:SubdlConverter')


class SubdlSubtitle(Subtitle):
    provider_name = 'subdl'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, download_link, file_id, release_names, uploader,
                 season=None, episode=None, absolute_episode=None, is_pack=False, is_direct_file=False,
                 is_ai_translation=False, ai_source_n_id=None, ai_source_language=None, ai_target_language=None):
        super().__init__(language)
        language = Language.rebuild(language, hi=hearing_impaired, forced=forced)

        self.season = season
        self.episode = episode
        self.absolute_episode = absolute_episode
        self.is_pack = is_pack
        self.is_direct_file = is_direct_file
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
        # On-demand AI translation candidate: no download_link yet — the file is
        # produced by the SubDL translation API when this subtitle is picked.
        self.is_ai_translation = is_ai_translation
        self.ai_source_n_id = ai_source_n_id
        self.ai_source_language = ai_source_language
        self.ai_target_language = ai_target_language
        if is_ai_translation:
            self.release_info = f'AI translation (SubDL) from {ai_source_language}: {self.release_info}'

    @property
    def id(self):
        return self.file_id

    def get_matches(self, video):
        matches = set()

        # handle movies and series separately
        if isinstance(video, Episode):
            # series
            matches.add('series')
            # episode — match by standard episode, absolute episode, or pack range
            matched_by_absolute = False
            if video.episode == self.episode:
                matches.add('episode')
            elif (getattr(video, 'absolute_episode', None) and
                  video.absolute_episode == self.episode):
                matches.add('episode')
                matched_by_absolute = True
            elif self.is_pack:
                # Pack was already validated to contain the target episode
                matches.add('episode')
            # season
            if video.season == self.season:
                matches.add('season')
            elif self.is_pack and self.absolute_episode:
                # Arc-based season numbering (e.g. subdl's Enies Lobby = S09) differs from
                # Sonarr's sequential numbering (S11). When a pack is validated via absolute
                # episode range, trust the match regardless of season number discrepancy.
                matches.add('season')
            elif matched_by_absolute:
                # Absolute episode numbering uniquely identifies the (season, episode) pair,
                # so trust the season too — handles anime uploads tagged with season=0 or
                # arc-based season numbering different from Sonarr's.
                matches.add('season')
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


class SubdlProvider(Provider):
    """Subdl Provider"""
    server_hostname = 'api.subdl.com'

    languages = {Language(*lang) for lang in list(language_converters['subdl'].to_subdl.keys())}
    languages.update(set(Language.rebuild(lang, forced=True) for lang in languages))
    languages.update(set(Language.rebuild(l, hi=True) for l in languages))

    video_types = (Episode, Movie)

    def __init__(self, api_key=None, ai_translate=False, include_ai_translated=False):
        if not api_key:
            raise ConfigurationError('Api_key must be specified')

        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}
        self.api_key = api_key
        self.ai_translate = ai_translate
        self.include_ai_translated = include_ai_translated
        self.video = None
        self._started = None
        # One informational log per video for AI-translate availability notices.
        self._ai_notices_logged = set()

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
            res = self.checked(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=(('api_key', self.api_key),
                                                 ('bazarr', 1),  # this argument filters incompatible image-based or
                                         # txt subtitles
                                                 ('comment', 1),
                                                 ('episode_number', self.video.episode),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('languages', langs),
                                                 ('releases', 1),
                                                 ('season_number', self.video.season),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('unpack', 1)),
                                         timeout=30)
            )

            # For anime with absolute episode numbering, also search by absolute episode number
            # so we can find subtitles that are only indexed by absolute number on subdl
            absolute_episode = getattr(self.video, 'absolute_episode', None)
            if absolute_episode and absolute_episode != self.video.episode:
                logger.debug(f'Also searching by absolute episode number: {absolute_episode}')
                res_absolute = self.checked(
                    lambda: self.session.get(self.server_url() + 'subtitles',
                                             params=(('api_key', self.api_key),
                                                     ('bazarr', 1),  # this argument filters incompatible image-based or
                                         # txt subtitles
                                                     ('comment', 1),
                                                     ('episode_number', absolute_episode),
                                                     ('film_name', title if not imdb_id else None),
                                                     ('imdb_id', imdb_id if imdb_id else None),
                                                     ('languages', langs),
                                                     ('releases', 1),
                                                     ('subs_per_page', 30),
                                                     ('type', 'tv'),
                                                     ('unpack', 1)),
                                             timeout=30)
                )
            else:
                res_absolute = None

            # Fallback: search by season only (no episode filter) to catch subtitles that use
            # split-season / cour-based internal numbering (e.g. Fire Force S3 split into two cours
            # where episode 25 is stored internally as cour-2 episode 13).
            # The release name matching in get_matches() will identify the correct episode.
            logger.debug(f'Also searching by season only (no episode filter) for season {self.video.season}')
            res_season = self.checked(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=(('api_key', self.api_key),
                                                 ('bazarr', 1),  # this argument filters incompatible image-based or
                                         # txt subtitles
                                                 ('comment', 1),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('languages', langs),
                                                 ('releases', 1),
                                                 ('season_number', self.video.season),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('unpack', 1)),
                                         timeout=30)
            )
        else:
            res_absolute = None
            res_season = None
            params = {
                       'api_key': self.api_key,
                       'bazarr': 1,  # this argument filters incompatible image-based or txt subtitles
                       'comment': 1,
                       'film_name': title if not imdb_id else None,
                       'imdb_id': imdb_id,
                       'languages': langs,
                       'releases': 1,
                       'subs_per_page': 30,
                       'type': 'movie',
            }
            res = self.checked(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=params,
                                         timeout=30)
            )

            # subdl also allows searching by TMDB ID, and some movies don't always
            # have the correct IMDB ID, or may not have it at all. We also search by TMDB ID
            # if it's available for the movie.
            if res.status_code == 200:
                # if the previous request with IMDb ID reported errors
                res_data = res.json()

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

                        res = self.checked(
                            lambda: self.session.get(self.server_url() + 'subtitles',
                                                     params=params,
                                                     timeout=30)
                        )

        subtitles = []

        result = res.json()

        # AI-translation availability for the requested languages (subdl api
        # returns this only for bazarr=1 requests; absent on older API versions).
        translation_block = result.get('translation') if isinstance(result, dict) else None

        if ('success' in result and not result['success']) or ('status' in result and not result['status']):
            logger.debug(result)
            if 'error' in result and "can't find" in result['error'].lower():
                logger.debug(f"No subtitles found for {imdb_id or title}: {result['error']}")
            else:
                logger.debug(f"Error while searching for subtitles: {result}")
            return subtitles

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
            res_title = self.checked(
                lambda: self.session.get(self.server_url() + 'subtitles',
                                         params=(('api_key', self.api_key),
                                                 ('film_name', title if not imdb_id else None),
                                                 ('imdb_id', imdb_id if imdb_id else None),
                                                 ('languages', langs),
                                                 ('subs_per_page', 30),
                                                 ('type', 'tv'),
                                                 ('comment', 1),
                                                 ('releases', 1),
                                                 ('unpack', 1),
                                                 ('bazarr', 1)),  # this argument filters incompatible image-based
                                         # or txt subtitles
                                         timeout=30)
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
                if item.get('ai_translated') and not self.include_ai_translated:
                    continue
                is_pack = False
                is_direct_file = False
                download_link = item['url']
                file_id = item['name']
                item_season = item.get('season', None)
                item_episode = item.get('episode', None)
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

                        # Prefer direct unpacked file when the API exposes one matching
                        # the target episode (unpack=1). This avoids downloading the whole
                        # season ZIP just to extract a single subtitle.
                        unpack_entry = next(
                            (f for f in item.get('unpack_files', [])
                             if f.get('episode') == self.video.episode
                             or (absolute_episode and f.get('episode') == absolute_episode)),
                            None
                        )
                        if unpack_entry:
                            download_link = unpack_entry['url']
                            file_id = f"{item['name']}/{unpack_entry['file_n_id']}"
                            item_season = unpack_entry.get('season', item_season)
                            item_episode = unpack_entry.get('episode', item_episode)
                            is_pack = False
                            is_direct_file = True
                            logger.debug(
                                f'Using unpacked file {unpack_entry["name"]} for episode '
                                f'{item_episode} instead of pack {item["name"]}'
                            )

                uploader = item.get('author', '')
                if item.get('ai_translated'):
                    uploader = f'{uploader} (AI translated)' if uploader else 'AI translated'

                subtitle = SubdlSubtitle(
                    language=Language.fromsubdl(item['language']),
                    forced=self._is_forced(item),
                    hearing_impaired=item.get('hi', False) or self._is_hi(item),
                    page_link=urljoin("https://subdl.com", item.get('subtitlePage', '')),
                    download_link=download_link,
                    file_id=file_id,
                    release_names=item.get('releases', []),
                    uploader=uploader,
                    season=item_season,
                    episode=item_episode,
                    absolute_episode=absolute_episode,
                    is_pack=is_pack,
                    is_direct_file=is_direct_file,
                )
                subtitle.get_matches(self.video)
                if subtitle.language in languages:  # make sure only desired subtitles variants are returned
                    subtitles.append(subtitle)

        self._add_ai_translation_candidates(translation_block, languages, subtitles)

        return subtitles

    def _log_ai_notice_once(self, message):
        key = (getattr(self.video, 'name', None) or getattr(self.video, 'title', ''), message)
        if key in self._ai_notices_logged:
            return
        self._ai_notices_logged.add(key)
        logger.info(message)

    def _add_ai_translation_candidates(self, translation, languages, subtitles):
        """Append virtual 'AI translation' candidates for wanted languages the
        API reported as missing but translatable (SubDL Plus/Pro feature)."""
        if not self.ai_translate or not isinstance(translation, dict):
            return

        missing = set(translation.get('missing_languages') or [])
        if not missing:
            return

        if not translation.get('entitled'):
            upgrade_url = translation.get('upgrade_url') or 'https://subdl.com/pro?ref=bazarr'
            self._log_ai_notice_once(
                f'subdl: missing languages ({", ".join(sorted(missing))}) can be AI-translated '
                f'in about a minute with a SubDL Plus/Pro subscription: {upgrade_url}')
            return

        sources = translation.get('sources') or []
        if not sources:
            reset_at = translation.get('quota_reset_at') or 'the 1st of next month'
            self._log_ai_notice_once(
                f'subdl: AI translation quota exhausted; more translations available after {reset_at}')
            return

        # Translations inherit the source subtitle's timing, so pick the source
        # whose release names best match the video.
        def source_score(source):
            matches = set()
            utils.update_matches(matches, self.video, source.get('releases') or [])
            return len(matches)

        best_source = max(sources, key=source_score)
        source_releases = best_source.get('releases') or []
        source_n_id = best_source.get('n_id')
        if not source_n_id:
            return

        existing_languages = {(sub.language.alpha3, sub.language.country, sub.language.script)
                              for sub in subtitles}

        for language in languages:
            # Only plain variants: a forced/HI subtitle can't be produced by
            # translating a regular source.
            if language.forced or getattr(language, 'hi', False):
                continue
            if (language.alpha3, language.country, language.script) in existing_languages:
                continue
            try:
                target_code = language_converters['subdl'].convert(
                    language.alpha3, language.country, language.script)
            except Exception:
                continue
            if target_code not in missing:
                continue

            season = self.video.season if isinstance(self.video, Episode) else None
            episode = self.video.episode if isinstance(self.video, Episode) else None

            candidate = SubdlSubtitle(
                language=language,
                forced=False,
                hearing_impaired=False,
                page_link='https://subdl.com/pro?ref=bazarr',
                download_link=None,
                file_id=f'ai:{source_n_id}:{target_code}',
                release_names=source_releases,
                uploader='SubDL AI',
                season=season,
                episode=episode,
                is_ai_translation=True,
                ai_source_n_id=source_n_id,
                ai_source_language=best_source.get('language') or '',
                ai_target_language=target_code,
            )
            candidate.get_matches(self.video)
            logger.debug(
                f'Offering AI translation candidate for {target_code} '
                f'from source {source_n_id} ({best_source.get("language")})')
            subtitles.append(candidate)

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

    # AI translation jobs normally finish in well under a minute; poll with a
    # generous ceiling so a slow job still lands in the same download call.
    AI_TRANSLATE_POLL_INTERVAL = 4
    AI_TRANSLATE_MIN_DEADLINE = 90
    AI_TRANSLATE_MAX_DEADLINE = 180

    def download_subtitle(self, subtitle):
        logger.debug('Downloading subtitle %r', subtitle)

        if getattr(subtitle, 'is_ai_translation', False):
            self._download_ai_translation(subtitle)
            return

        download_link = urljoin("https://dl.subdl.com", subtitle.download_link)

        r = self.checked(
            lambda: self.session.get(download_link, timeout=30)
        )

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
            elif subtitle.is_direct_file:
                # subdl unpack=1: response is a raw subtitle file, not a ZIP
                subtitle.content = fix_line_ending(r.content)
            else:
                logger.error(f'Could not unzip subtitle from {download_link}')
                subtitle.content = None
                return

    @staticmethod
    def _safe_json(response):
        try:
            payload = response.json()
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _download_ai_translation(self, subtitle):
        """Submit a translation job for the chosen source subtitle, wait for it
        and return the translated file.

        Failures set subtitle.content to None instead of raising: a missed
        translation must never throttle the provider's regular downloads. If
        the deadline passes, the job still finishes server-side — the result is
        published as a regular subtitle and any retry is answered instantly
        from the finished job (no extra quota).
        """
        base = self.server_url()
        params = {'api_key': self.api_key}
        subtitle.content = None

        try:
            response = self.session.post(
                base + 'pro/translate/subtitles',
                params=params,
                json={'n_id': subtitle.ai_source_n_id,
                      'target_language': subtitle.ai_target_language},
                timeout=30,
            )
        except Exception:
            logger.exception('subdl: AI translation request failed')
            return

        if response.status_code not in (200, 202):
            payload = self._safe_json(response)
            error = payload.get('error')
            message = payload.get('message') or error or f'HTTP {response.status_code}'
            if error == 'translation_quota_exhausted':
                self._log_ai_notice_once(
                    'subdl: AI translation quota exhausted; more translations available next month')
            elif error == 'translation_not_entitled':
                self._log_ai_notice_once(
                    'subdl: AI translation requires a SubDL Plus/Pro subscription: '
                    'https://subdl.com/pro?ref=bazarr')
            else:
                logger.error(f'subdl: AI translation request rejected: {message}')
            return

        payload = self._safe_json(response)
        request_id = payload.get('request_id')
        if not request_id:
            logger.error(f'subdl: AI translation response missing request_id: {payload}')
            return

        job = payload.get('job') or {}
        estimated_ms = payload.get('estimated_duration_ms') or job.get('eta_ms') or 60000
        deadline_seconds = min(
            max((estimated_ms / 1000.0) * 2, self.AI_TRANSLATE_MIN_DEADLINE),
            self.AI_TRANSLATE_MAX_DEADLINE,
        )
        deadline = time.time() + deadline_seconds
        download_ready = bool(job.get('download_ready'))
        poll_failures = 0

        logger.debug(
            f'subdl: AI translation job {request_id} submitted '
            f'(estimated {estimated_ms / 1000.0:.0f}s, deadline {deadline_seconds:.0f}s, '
            f'reused={payload.get("reused")})')

        while not download_ready and time.time() < deadline:
            time.sleep(self.AI_TRANSLATE_POLL_INTERVAL)
            try:
                poll = self.session.get(
                    f'{base}pro/translate/jobs/{request_id}', params=params, timeout=30)
            except Exception:
                poll_failures += 1
                if poll_failures >= 5:
                    logger.exception('subdl: AI translation polling failed repeatedly')
                    return
                continue

            if poll.status_code != 200:
                poll_failures += 1
                if poll_failures >= 5:
                    logger.error(
                        f'subdl: AI translation polling failed repeatedly '
                        f'(HTTP {poll.status_code})')
                    return
                continue

            poll_failures = 0
            job = self._safe_json(poll).get('job') or {}
            if job.get('status') == 'failed':
                logger.error(f'subdl: AI translation job {request_id} failed: {job.get("error")}')
                return
            download_ready = bool(job.get('download_ready'))

        if not download_ready:
            logger.info(
                f'subdl: AI translation job {request_id} still running; the finished '
                f'translation will be available as a regular subtitle on the next search')
            return

        try:
            download = self.session.get(
                f'{base}pro/translate/jobs/{request_id}/download', params=params, timeout=30)
        except Exception:
            logger.exception('subdl: AI translation download failed')
            return

        if download.status_code != 200 or not download.content:
            logger.error(
                f'subdl: AI translation download failed (HTTP {download.status_code})')
            return

        subtitle.content = fix_line_ending(download.content)
        logger.debug(f'subdl: AI translation job {request_id} downloaded')

    def checked(self, fn: Callable, is_retry: bool = False, retry_attempt=0) -> Response:
        """
        Executes a given callable and handles API-related errors, including authentication errors, rate limits,
        and service busy scenarios. The method will ensure proper handling of retries and logging for recoverable
        errors or failures.

        :param fn: The callable to execute, expected to return a Response object.
        :type fn: Callable
        :param is_retry: Indicates whether the current execution is a retry attempt. Defaults to False.
        :type is_retry: bool, optional
        :param retry_attempt: The number of retry attempts made for handling "service_busy" errors. Defaults to 0.
        :type retry_attempt: int, optional
        :return: The HTTP response object returned by the callable upon success.
        :rtype: Response
        :raises ProviderError: If a non-recoverable error or unhandled exception occurs.
        :raises AuthenticationError: If the API key is invalid with a 403 response code.
        :raises DownloadLimitExceeded: If the daily download limit is exceeded.
        :raises APIThrottled: If the API request rate limit is hit and retries are exhausted.
        """
        response = None
        try:
            response = fn()
        except Exception:
            logger.exception('Unhandled exception raised.')
            raise
        else:
            status_code = response.status_code
            if status_code == 402:
                # Payment required: this request needs an active paid SubDL
                # subscription. Retrying won't help until the user upgrades.
                message = "Active paid SubDL subscription required"
                payload = self._safe_json(response)
                if payload.get('message'):
                    message = payload['message']
                raise ProviderError(message)
            elif status_code == 403:
                raise AuthenticationError("Invalid API key")
            elif status_code == 404:
                raise ProviderError("Resource not found")
            elif status_code == 429:
                try:
                    payload = response.json()
                except Exception:
                    logger.exception('Failed to parse JSON response')
                else:
                    if isinstance(payload, dict) and 'error' in payload:
                        if payload['error'] in ['daily_limit', 'api_download_limit_exceeded']:
                            raise DownloadLimitExceeded("Daily download limit exceeded")
                        elif payload['error'] == 'rate_limit':
                            if not is_retry:
                                logger.debug("API request rate limit hit, waiting and trying again once.")
                                retry_delay = response.headers.get('Retry-After', 15)
                                logger.debug(f"Retry delay: {retry_delay} seconds")
                                time.sleep(int(retry_delay))
                                logger.debug("Retrying API request")
                                return self.checked(fn, is_retry=True)
                            raise APIThrottled("API request limit hit")
                        elif payload['error'] == 'service_busy':
                            if retry_attempt < 5:
                                logger.debug("API service is busy, waiting and trying again once.")
                                retry_delay = response.headers.get('Retry-After', 5)
                                logger.debug(f"Service busy retry delay: {retry_delay} seconds")
                                time.sleep(int(retry_delay))
                                logger.debug("Retrying service busy API request")
                                return self.checked(fn, retry_attempt=retry_attempt + 1)
                            else:
                                raise ProviderError("API service is busy")
                    else:
                        logger.exception(f'Missing error field in JSON response: {payload}')
                        response.raise_for_status()
            elif status_code != 200:
                logger.exception('Unhandled API response')
                response.raise_for_status()

        return response
