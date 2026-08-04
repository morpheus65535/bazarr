# -*- coding: utf-8 -*-
import logging
import os
import re
import time
import io
from threading import Lock
from typing import Callable

from zipfile import ZipFile, is_zipfile
from rarfile import RarFile, is_rarfile
from urllib.parse import urljoin
from requests import Session, Response
from requests.exceptions import RequestException
from guessit import guessit

from babelfish import language_converters
from subzero.language import Language
from subliminal import Episode, Movie
from subliminal.exceptions import (ConfigurationError, ProviderError, DownloadLimitExceeded, AuthenticationError,
                                   ServiceUnavailable)
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider
from subliminal_patch.providers import utils

logger = logging.getLogger(__name__)

language_converters.register('subdl = subliminal_patch.converters.subdl:SubdlConverter')


class SubdlRequestRejected(ProviderError):
    """One request was refused for a reason specific to that request.

    Raised for 4xx responses that say nothing about the provider's health — a
    title the API refuses to parse, a subtitle that no longer exists. It must be
    handled inside this provider: bazarr throttles on *any* exception that
    escapes (10 minutes by default, see app/get_providers.py:provider_throttle),
    and one dead download link is not a reason to stop using subdl.
    """


class SubdlSubtitle(Subtitle):
    provider_name = 'subdl'
    hash_verifiable = False
    hearing_impaired_verifiable = True

    def __init__(self, language, forced, hearing_impaired, page_link, download_link, file_id, release_names, uploader,
                 season=None, episode=None, absolute_episode=None, is_pack=False, is_direct_file=False,
                 is_full_season=False, episode_title=None, target_episode=None,
                 matched_id=False, matched_title=False,
                 is_ai_translation=False, ai_source_n_id=None, ai_source_language=None, ai_target_language=None):
        super().__init__(language)
        language = Language.rebuild(language, hi=hearing_impaired, forced=forced)

        self.season = season
        self.episode = episode
        self.absolute_episode = absolute_episode
        self.is_pack = is_pack
        self.is_direct_file = is_direct_file
        # A pack covering a whole season carries no episode range: every episode
        # of `season` is inside it, so the archive must be searched by episode.
        self.is_full_season = is_full_season
        # The episode we are searching FOR. Distinct from self.episode, which is
        # whatever the API said about the item — for a pack that is the pack's
        # own field (often None), so extracting on it would pull an arbitrary
        # member out of a season archive.
        self.target_episode = target_episode
        # Carried so download_subtitle can match a pack member by episode title
        # without reaching back into shared provider state.
        self.episode_title = episode_title
        # Whether this result is actually backed by an id match, rather than by a
        # fuzzy film_name/title search. Only an id-matched result may claim the
        # imdb_id/tmdb_id/series_imdb_id matches, which are worth a large score.
        self.matched_id = matched_id
        self.matched_title = matched_title
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
            # series — only when the result is tied to the series by id. A
            # film_name search is fuzzy server-side and can return a different
            # show, and 'series' alone satisfies bazarr's series/episode guard.
            if self.matched_id and video.series_imdb_id:
                matches.add('series')
                matches.add('series_imdb_id')
                # An IMDB match also confirms the year.
                if video.year:
                    matches.add('year')
            elif self.matched_title:
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
        else:
            # title/imdb/tmdb — again only what the search actually established.
            if self.matched_id:
                if video.imdb_id:
                    matches.add('imdb_id')
                if video.tmdb_id:
                    matches.add('tmdb_id')
                matches.add('title')
                if video.year:
                    matches.add('year')
            elif self.matched_title:
                matches.add('title')

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
        self._started = None
        # One informational log per video for AI-translate availability notices.
        # Bazarr shares one provider instance across threads, so guard the set.
        self._ai_notices_logged = set()
        self._ai_notices_lock = Lock()

    def initialize(self):
        self._started = time.time()

    def terminate(self):
        self.session.close()

    def server_url(self):
        return f'https://{self.server_hostname}/api/v1/'

    # The API caps subs_per_page at 30, so a popular title is truncated. Paging
    # is deliberately shallow and only applied to the primary search: every page
    # is a request against the caller's daily API quota (2000-30000/day), and a
    # library-wide scan issues one search per episode. One extra page, only when
    # the first came back full, keeps the worst case at ~1.5x the old request
    # count instead of 2.5x.
    SUBS_PER_PAGE = 30
    MAX_PAGES = 2

    # The API rejects these outright ("Film name contains potentially unsafe
    # characters"), which would otherwise 400 every apostrophe title such as
    # "Grey's Anatomy" and get the whole provider throttled.
    # Every one of these becomes a SPACE, never nothing. The search index stores
    # "Grey's Anatomy" as the tokens grey|s|anatomy, so deleting the apostrophe
    # would query "greys" and match nothing -- verified against the live API,
    # where "Schitts Creek" returns 0 results and "Schitt s Creek" returns 8.
    UNSAFE_TITLE_CHARS = re.compile(r'''[<>{}\[\]'"`´’;\\/]''')

    @classmethod
    def _sanitize_title(cls, title):
        if not title:
            return title
        cleaned = cls.UNSAFE_TITLE_CHARS.sub(' ', title)
        cleaned = ' '.join(cleaned.split())
        if cleaned != title:
            logger.debug(f'Sanitized title for search: {title!r} -> {cleaned!r}')
        return cleaned

    @staticmethod
    def _is_error_payload(payload):
        if not isinstance(payload, dict):
            return True
        if 'success' in payload and not payload['success']:
            return True
        if 'status' in payload and not payload['status']:
            return True
        return False

    def _search(self, params, description, paginate=False):
        """Run one search and return (items, first_payload).

        Never raises for this single search: a failure here must not discard
        results already gathered by the other searches, nor throttle the whole
        provider.

        Only per-request and transport failures are absorbed. Anything that
        describes the state of the ACCOUNT or the service — an invalid key, the
        daily download limit, a rate limit, an outage — is re-raised so bazarr
        can throttle and back off. Swallowing those would leave a client with a
        revoked key searching forever at full rate.
        """
        items = []
        first_payload = {}
        page = 1
        while page <= (self.MAX_PAGES if paginate else 1):
            call_params = dict(params)
            call_params['subs_per_page'] = self.SUBS_PER_PAGE
            if page > 1:
                call_params['page'] = page
            try:
                response = self.checked(
                    lambda: self.session.get(self.server_url() + 'subtitles',
                                             params=call_params, timeout=30)
                )
            except (SubdlRequestRejected, RequestException) as error:
                # The api_key rides in the request URL, and requests puts that
                # URL in the exception text.
                logger.debug(f'subdl: {description} search failed, continuing '
                             f'without it: {self._redact(repr(error))}')
                break

            payload = self._safe_json(response)
            if page == 1:
                first_payload = payload
            if self._is_error_payload(payload):
                error = payload.get('error') if isinstance(payload, dict) else None
                if error and "can't find" in str(error).lower():
                    logger.debug(f'subdl: {description} search found nothing: {error}')
                else:
                    logger.debug(f'subdl: {description} search returned an error payload: {payload}')
                break

            batch = payload.get('subtitles') or []
            items.extend(batch)
            total_pages = payload.get('totalPages') or 1
            if not paginate or page >= total_pages or len(batch) < self.SUBS_PER_PAGE:
                break
            page += 1

        return items, first_payload

    def query(self, languages, video):
        if isinstance(video, Episode):
            title = video.series
        else:
            title = video.title
        title = self._sanitize_title(title)

        imdb_id = None
        tmdb_id = None
        if isinstance(video, Episode) and video.series_imdb_id:
            imdb_id = video.series_imdb_id
        elif isinstance(video, Movie):
            if video.imdb_id:
               imdb_id = video.imdb_id
            if video.tmdb_id:
               tmdb_id = video.tmdb_id

        # be sure to remove duplicates using list(set())
        langs_list = sorted(list(set([language_converters['subdl'].convert(lang.alpha3, lang.country, lang.script) for
                                      lang in languages])))

        langs = ','.join(langs_list)
        logger.debug(f'Searching for those languages: {langs}')

        # 'bazarr' filters incompatible image-based or txt subtitles.
        base_params = {
            'api_key': self.api_key,
            'bazarr': 1,
            'comment': 1,
            'languages': langs,
            'releases': 1,
            'unpack': 1,
        }
        if imdb_id:
            base_params['imdb_id'] = imdb_id
        else:
            base_params['film_name'] = title

        # Results found via an id-based search may claim the id matches; results
        # found only by (fuzzy, server-side) film_name may not.
        matched_id = bool(imdb_id)
        matched_title = not imdb_id

        all_items = []
        seen_ids = set()

        def merge(items, description):
            added = 0
            for item in items:
                key = item.get('subtitlePage') or item.get('name')
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                all_items.append(item)
                added += 1
            if added:
                logger.debug(f'subdl: {description} search added {added} subtitles')
            return added

        if isinstance(video, Episode):
            episode_items, first_payload = self._search(
                dict(base_params, type='tv', episode_number=video.episode, season_number=video.season),
                'episode', paginate=True)
            merge(episode_items, 'episode')

            # For anime with absolute episode numbering, also search by absolute episode number
            # so we can find subtitles that are only indexed by absolute number on subdl
            absolute_episode = getattr(video, 'absolute_episode', None)
            if absolute_episode and absolute_episode != video.episode:
                logger.debug(f'Also searching by absolute episode number: {absolute_episode}')
                merge(self._search(dict(base_params, type='tv', episode_number=absolute_episode),
                                   'absolute episode')[0], 'absolute episode')

            # Fallback: search by season only (no episode filter) to catch subtitles that use
            # split-season / cour-based internal numbering (e.g. Fire Force S3 split into two cours
            # where episode 25 is stored internally as cour-2 episode 13).
            # The release name matching in get_matches() will identify the correct episode.
            logger.debug(f'Also searching by season only (no episode filter) for season {video.season}')
            # Not paginated: this is a supplementary fallback, and paging it
            # would double the per-episode request cost of a full library scan.
            merge(self._search(dict(base_params, type='tv', season_number=video.season),
                               'season-only')[0], 'season-only')

            # Last resort: if all season-filtered searches returned nothing, search by title only
            # (no season/episode filter). This catches anime stored as season 0 on subdl (full series
            # blocks) where season_number filtering silently excludes all results.
            if not all_items:
                logger.debug('All season-filtered searches returned 0 results, falling back to title-only search')
                merge(self._search(dict(base_params, type='tv'), 'title-only')[0], 'title-only')
        else:
            movie_items, first_payload = self._search(dict(base_params, type='movie'), 'movie', paginate=True)
            merge(movie_items, 'movie')

            # subdl also allows searching by TMDB ID, and some movies don't always
            # have the correct IMDB ID, or may not have it at all. We also search by TMDB ID
            # if it's available for the movie.
            if not all_items and tmdb_id:
                logger.debug('No subtitles found via IMDb id or film name. Search instead with TMDB id')
                tmdb_params = dict(base_params, type='movie', tmdb_id=tmdb_id)
                tmdb_params.pop('film_name', None)
                tmdb_params.pop('imdb_id', None)
                tmdb_items, tmdb_payload = self._search(tmdb_params, 'tmdb', paginate=True)
                if merge(tmdb_items, 'tmdb'):
                    matched_id = True
                    matched_title = False
                if not first_payload:
                    first_payload = tmdb_payload
            elif not all_items:
                logger.debug('No subtitles found via IMDb id or film name. TMDB ID unavailable for fallback')

        subtitles = []

        # AI-translation availability for the requested languages (subdl api
        # returns this only for bazarr=1 requests; absent on older API versions).
        translation_block = first_payload.get('translation') if isinstance(first_payload, dict) else None

        logger.debug(f"Query returned {len(all_items)} subtitles")

        absolute_episode = getattr(video, 'absolute_episode', None)

        for item in all_items:
            if item.get('ai_translated') and not self.include_ai_translated:
                continue

            # A language the converter does not know must cost us this one item,
            # not the whole search (an escaping ConfigurationError bans subdl 12h).
            try:
                language = Language.fromsubdl(item['language'])
            except Exception:
                logger.debug(f"Skipping subtitle with unsupported language {item.get('language')!r}")
                continue

            is_pack = False
            is_direct_file = False
            is_full_season = False
            download_link = item['url']
            # Keep the archive name as the public id: bazarr persists it in the
            # blacklist and in history, so changing it would silently invalidate
            # every existing subdl blacklist entry. Uniqueness is handled by
            # deduping on subtitlePage in merge() instead.
            file_id = item['name']
            item_season = item.get('season', None)
            item_episode = item.get('episode', None)

            if isinstance(video, Episode):
                ep_from = self._episode_number(item.get('episode_from'))
                ep_end = self._episode_number(item.get('episode_end'))
                is_full_season = bool(item.get('full_season'))

                # Only fall back to parsing release names when the API gave us
                # nothing. For a single-episode row it returns ep_from == ep_end,
                # which is authoritative and must not be overridden by a batch
                # release name that happens to mention a range.
                if ep_from is None and ep_end is None and not is_full_season:
                    ep_from_parsed, ep_end_parsed = self._parse_episode_range_from_releases(
                        item.get('releases', [])
                    )
                    if ep_from_parsed and ep_end_parsed and ep_from_parsed != ep_end_parsed:
                        ep_from = ep_from_parsed
                        ep_end = ep_end_parsed
                        logger.debug(
                            f'Parsed episode range {ep_from}-{ep_end} from release names'
                        )

                has_range = ep_from is not None and ep_end is not None and ep_from != ep_end
                if has_range:
                    # Multi-episode pack: allow if target episode is within range
                    target_ep = video.episode
                    if absolute_episode:
                        # Check both standard and absolute episode against the range
                        if not ((ep_from <= target_ep <= ep_end) or
                                (ep_from <= absolute_episode <= ep_end)):
                            continue
                    else:
                        if not (ep_from <= target_ep <= ep_end):
                            continue

                # A full-season pack carries no range (the API sends
                # episode_from=null, episode_end=0, full_season=true) but does
                # contain every episode of item['season'].
                if has_range or is_full_season:
                    is_pack = True

                    # Prefer the per-episode file the server already extracted
                    # (unpack=1). Downloading a whole season archive client-side
                    # is the fallback, not the plan.
                    unpack_entry = next(
                        (f for f in item.get('unpack_files') or []
                         if f.get('episode') == video.episode
                         or (absolute_episode and f.get('episode') == absolute_episode)),
                        None
                    )
                    if unpack_entry:
                        download_link = unpack_entry['url']
                        file_id = f"{item['name']}/{unpack_entry['file_n_id']}"
                        # `or` not `.get(default)`: the API sends season/episode
                        # as 0 rather than omitting them, so a dict default never
                        # applies and a correct season would be overwritten by 0.
                        item_season = unpack_entry.get('season') or item_season
                        item_episode = unpack_entry.get('episode') or item_episode
                        is_pack = False
                        is_full_season = False
                        is_direct_file = True
                        logger.debug(
                            f'Using unpacked file {unpack_entry["name"]} for episode '
                            f'{item_episode} instead of pack {item["name"]}'
                        )

            uploader = item.get('author', '')
            if item.get('ai_translated'):
                uploader = f'{uploader} (AI translated)' if uploader else 'AI translated'

            subtitle = SubdlSubtitle(
                language=language,
                forced=self._is_forced(item),
                hearing_impaired=self._is_hearing_impaired(item),
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
                is_full_season=is_full_season,
                episode_title=getattr(video, 'title', None) if isinstance(video, Episode) else None,
                target_episode=video.episode if isinstance(video, Episode) else None,
                matched_id=matched_id,
                matched_title=matched_title,
            )
            subtitle.get_matches(video)
            if subtitle.language in languages:  # make sure only desired subtitles variants are returned
                subtitles.append(subtitle)

        self._add_ai_translation_candidates(translation_block, languages, subtitles, video,
                                            matched_id=matched_id, matched_title=matched_title)

        return subtitles

    def _log_ai_notice_once(self, scope, message):
        """Log an AI-translate notice once per (video-or-subtitle, message).

        Bazarr searches every wanted item in a loop; without this the same
        upgrade notice would be written once per item.
        """
        key = (getattr(scope, 'name', None) or getattr(scope, 'id', None)
               or getattr(scope, 'title', ''), message)
        with self._ai_notices_lock:
            if key in self._ai_notices_logged:
                return
            self._ai_notices_logged.add(key)
        logger.info(message)

    def _add_ai_translation_candidates(self, translation, languages, subtitles, video,
                                       matched_id=False, matched_title=False):
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
                video,
                f'subdl: missing languages ({", ".join(sorted(missing))}) can be AI-translated '
                f'in about a minute with a SubDL Plus/Pro subscription: {upgrade_url}')
            return

        sources = translation.get('sources') or []
        if not sources:
            reset_at = translation.get('quota_reset_at') or 'the 1st of next month'
            self._log_ai_notice_once(
                video,
                f'subdl: AI translation quota exhausted; more translations available after {reset_at}')
            return

        # The server already orders sources deliberately (English first for
        # translation quality, non-HI before HI). Keep that order and only use
        # release-name matching to break ties, since translations inherit the
        # source subtitle's timing.
        def source_rank(indexed_source):
            index, source = indexed_source
            matches = set()
            utils.update_matches(matches, video, source.get('releases') or [])
            return (-len(matches), index)

        best_source = min(enumerate(sources), key=source_rank)[1]
        source_releases = best_source.get('releases') or []
        source_n_id = best_source.get('n_id')
        if not source_n_id:
            return
        # A translation of an SDH source is still SDH; declaring it non-HI on a
        # hearing_impaired_verifiable provider would mislabel the saved file.
        source_is_hi = bool(best_source.get('hi'))

        existing_languages = {(sub.language.alpha3, sub.language.country, sub.language.script,
                               bool(getattr(sub.language, 'hi', False)), bool(sub.language.forced))
                              for sub in subtitles}

        for language in languages:
            # A forced subtitle can't be produced by translating a regular source.
            if language.forced:
                continue
            # An HI target can only come from an HI source, and vice versa.
            if bool(getattr(language, 'hi', False)) != source_is_hi:
                continue
            if (language.alpha3, language.country, language.script,
                    bool(getattr(language, 'hi', False)), False) in existing_languages:
                continue
            try:
                target_code = language_converters['subdl'].convert(
                    language.alpha3, language.country, language.script)
            except Exception:
                continue
            if target_code not in missing:
                continue

            season = video.season if isinstance(video, Episode) else None
            episode = video.episode if isinstance(video, Episode) else None

            candidate = SubdlSubtitle(
                language=language,
                forced=False,
                hearing_impaired=source_is_hi,
                page_link='https://subdl.com/pro?ref=bazarr',
                download_link=None,
                file_id=f'ai:{source_n_id}:{target_code}',
                release_names=source_releases,
                uploader='SubDL AI',
                season=season,
                episode=episode,
                matched_id=matched_id,
                matched_title=matched_title,
                is_ai_translation=True,
                ai_source_n_id=source_n_id,
                ai_source_language=best_source.get('language') or '',
                ai_target_language=target_code,
            )
            candidate.get_matches(video)
            logger.debug(
                f'Offering AI translation candidate for {target_code} '
                f'from source {source_n_id} ({best_source.get("language")})')
            subtitles.append(candidate)

    # 'HI'/'SDH' as whole words only. Bare substrings used to match inside
    # ordinary release groups — ' hi' fires on "Hive-CM8", "Hi10P" and "Hindi" —
    # which mislabels a normal subtitle as hearing-impaired and then hides it
    # from every non-HI language profile.
    _HI_WORD_RE = re.compile(
        r'(?<![a-z0-9])(hi|sdh|cc)(?![a-z0-9])'
        r'|_hi_|𝓢𝓓𝓗'
        r'|hearing[\s._-]?impaired'
        r'|closed[\s._-]?caption',
        re.IGNORECASE)
    _NON_HI_RE = re.compile(
        r'(?<![a-z0-9])(non[\s._-]?(hi|sdh)|(hi|sdh)[\s._-]?remove[d]?|remove[d]?[\s._-]?(hi|sdh))(?![a-z0-9])',
        re.IGNORECASE)
    _FORCED_RE = re.compile(r'(?<![a-z0-9])(forced|foreign[\s._-]?parts?)(?![a-z0-9])', re.IGNORECASE)

    @classmethod
    def _is_hearing_impaired(cls, item):
        """Combine the API's own hi flag with the text heuristics.

        The explicit non-HI markers win over both, so a subtitle whose comment
        says "removed SDH" is never stored as HI even when the API flags it.
        """
        if cls._is_explicit_non_hi(item):
            return False
        if item.get('hi', False):
            return True
        return cls._is_hi(item)

    @classmethod
    def _is_explicit_non_hi(cls, item):
        for text in cls._item_texts(item):
            if cls._NON_HI_RE.search(text):
                return True
        return False

    @staticmethod
    def _item_texts(item):
        texts = [item.get('comment') or '', item.get('name') or '']
        texts.extend(x for x in (item.get('releases') or []) if isinstance(x, str))
        return texts

    @classmethod
    def _is_hi(cls, item):
        # Comments include specific mention of removed or non HI
        if cls._is_explicit_non_hi(item):
            return False

        for text in cls._item_texts(item):
            if cls._HI_WORD_RE.search(text):
                return True

        # nothing match so we consider it as non-HI
        return False

    @classmethod
    def _is_forced(cls, item):
        # Forced markers appear in release names at least as often as in
        # comments, so read both. 'foreign' alone is too loose — it matches
        # ordinary descriptions — hence 'foreign part(s)'.
        for text in cls._item_texts(item):
            if cls._FORCED_RE.search(text):
                return True

        # nothing match so we consider it as normal subtitles
        return False

    @staticmethod
    def _episode_number(value):
        """Normalise an episode field to a positive int, or None.

        The API sends 0 (and sometimes null) to mean 'not applicable', so 0 must
        never be treated as episode zero nor as a usable range bound.
        """
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
        return number if number > 0 else None

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

    @staticmethod
    def _redact(url):
        """Strip the api_key before a URL reaches the log.

        Bazarr's log redactor only knows `apikey=`, so a subdl `api_key=` would
        otherwise be written to bazarr.log in cleartext — and those logs get
        pasted into public issues.
        """
        return re.sub(r'(api_key=)[^&\s]+', r'\1<redacted>', str(url))

    # AI translation jobs normally finish in well under a minute; poll with a
    # generous ceiling so a slow job still lands in the same download call.
    AI_TRANSLATE_POLL_INTERVAL = 4
    AI_TRANSLATE_MIN_DEADLINE = 90
    AI_TRANSLATE_MAX_DEADLINE = 180

    @staticmethod
    def _open_archive(stream):
        """Return an open ZipFile/RarFile, or None if the payload is neither.

        subdl serves some older uploads as RAR under a .zip filename and an
        application/octet-stream content type, so sniff the bytes rather than
        trusting either.
        """
        stream.seek(0)
        if is_zipfile(stream):
            stream.seek(0)
            return ZipFile(stream)
        stream.seek(0)
        try:
            if is_rarfile(stream):
                stream.seek(0)
                return RarFile(stream)
        except Exception:
            logger.debug('subdl: payload looked like RAR but could not be opened', exc_info=True)
        return None

    @staticmethod
    def _first_subtitle_in_archive(archive):
        """Pick a single subtitle member, ignoring archive junk.

        Skips directory entries and macOS AppleDouble resource forks
        (__MACOSX/._name.srt), which otherwise win the extension test and yield
        a few KB of binary instead of a subtitle.
        """
        for name in archive.namelist():
            if name.endswith('/'):
                continue
            base = name.rsplit('/', 1)[-1]
            if not base or base.startswith('._') or name.startswith('__MACOSX/'):
                continue
            if base.lower().endswith(('.srt', '.sub', '.ssa', '.ass')):
                return fix_line_ending(archive.read(name))
        return None

    def download_subtitle(self, subtitle):
        logger.debug('Downloading subtitle %r', subtitle)

        if getattr(subtitle, 'is_ai_translation', False):
            self._download_ai_translation(subtitle)
            return

        download_link = urljoin("https://dl.subdl.com", subtitle.download_link)
        safe_link = self._redact(download_link)

        subtitle.content = None
        try:
            r = self.checked(
                lambda: self.session.get(download_link, timeout=30)
            )
        except SubdlRequestRejected as error:
            # A subtitle that no longer exists fails this download only; bazarr
            # falls through to the next candidate.
            logger.warning(f'subdl: download rejected for {safe_link}: {error}')
            return

        if r is None or not r.content:
            logger.error(f'Could not download subtitle from {safe_link}')
            return

        archive = self._open_archive(io.BytesIO(r.content))
        if archive is None:
            if subtitle.is_direct_file:
                # subdl unpack=1: response is a raw subtitle file, not an archive
                subtitle.content = fix_line_ending(r.content)
            else:
                logger.error(f'Could not open subtitle archive from {safe_link}')
            return

        # A corrupt archive, or a RAR when bazarr could not find its unrar binary
        # (init.py sets rarfile.UNRAR_TOOL = None in that case), raises out of
        # archive.read(). bazarr treats rarfile.BadRarFile as a reason to throttle
        # the whole provider, so absorb it here: one unreadable archive is a
        # per-subtitle problem.
        try:
            self._extract(subtitle, archive, safe_link)
        except Exception as error:
            logger.warning(f'subdl: could not read archive {safe_link}: {self._redact(repr(error))}')
            subtitle.content = None

    def _extract(self, subtitle, archive, safe_link):
        if subtitle.is_pack or subtitle.is_full_season:
            # Match by episode number inside the archive. Only reached when the
            # server did not already expose the individual file via unpack=1.
            target_episode = subtitle.target_episode or subtitle.absolute_episode
            content = utils.get_subtitle_from_archive(
                archive,
                episode=target_episode,
                episode_title=subtitle.episode_title,
            )
            # Fallback: try absolute episode number
            if content is None and subtitle.absolute_episode:
                content = utils.get_subtitle_from_archive(
                    archive,
                    episode=subtitle.absolute_episode,
                )
            if content is None:
                logger.warning(
                    f'Could not find episode {target_episode} in pack archive {safe_link}')
                return
            subtitle.content = content
            return

        content = self._first_subtitle_in_archive(archive)
        if content is None:
            logger.error(f'No subtitle file found inside archive {safe_link}')
            return
        subtitle.content = content

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

        # Season/episode, not a file id: the server holds the subtitle files and
        # resolves which one to translate itself, extracting a season pack when
        # it has to. The client has no business shipping file ids or contents.
        payload_body = {'n_id': subtitle.ai_source_n_id,
                        'target_language': subtitle.ai_target_language}
        if subtitle.season is not None:
            payload_body['season'] = subtitle.season
        if subtitle.episode is not None:
            payload_body['episode'] = subtitle.episode

        try:
            response = self.session.post(
                base + 'pro/translate/subtitles',
                params=params,
                json=payload_body,
                timeout=30,
            )
        except Exception as error:
            logger.error(f'subdl: AI translation request failed: {self._redact(error)}')
            return

        if response.status_code not in (200, 202):
            payload = self._safe_json(response)
            error = payload.get('error')
            message = payload.get('message') or error or f'HTTP {response.status_code}'
            if error == 'translation_quota_exhausted':
                self._log_ai_notice_once(
                    subtitle,
                    'subdl: AI translation quota exhausted; more translations available next month')
            elif error == 'translation_not_entitled':
                self._log_ai_notice_once(
                    subtitle,
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
            except RequestException as error:
                poll_failures += 1
                if poll_failures >= 5:
                    logger.error('subdl: AI translation polling failed repeatedly: '
                                 f'{self._redact(repr(error))}')
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
        except RequestException as error:
            logger.error(f'subdl: AI translation download failed: {self._redact(repr(error))}')
            return

        if download.status_code != 200 or not download.content:
            logger.error(
                f'subdl: AI translation download failed (HTTP {download.status_code})')
            return

        subtitle.content = fix_line_ending(download.content)
        logger.debug(f'subdl: AI translation job {request_id} downloaded')

    # Absolute ceiling across BOTH retry branches. Previously rate_limit reset
    # the service_busy counter and vice versa, so an alternating server could
    # keep one search thread sleeping indefinitely.
    MAX_RETRY_ATTEMPTS = 6

    @staticmethod
    def _sleep_for_retry(response, default, label):
        raw = response.headers.get('Retry-After', default)
        try:
            delay = int(raw)
        except (TypeError, ValueError):
            # Retry-After may be an HTTP-date; int() would raise and abort.
            delay = default
        delay = max(0, min(delay, 60))
        logger.debug(f'{label} retry delay: {delay} seconds')
        time.sleep(delay)

    def checked(self, fn: Callable, is_retry: bool = False, retry_attempt=0, attempts=0) -> Response:
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
        except Exception as error:
            logger.error(f'Unhandled exception raised: {self._redact(error)}')
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
                # Only an auth verdict from the API itself should disable the
                # provider for 12 hours; an edge/WAF 403 is transient.
                payload = self._safe_json(response)
                error = str(payload.get('error') or payload.get('message') or '').lower()
                # Only a JSON verdict from our own API may disable the provider
                # for 12 hours. A 403 with no parseable body is an edge/WAF
                # challenge — transient, and not a statement about the key.
                if payload and ('key' in error or 'auth' in error or 'forbidden' in error):
                    raise AuthenticationError("Invalid API key")
                raise APIThrottled(f"Request rejected with 403: {error or 'no reason given'}")
            elif status_code == 404:
                raise SubdlRequestRejected("Resource not found")
            elif status_code == 429:
                payload = self._safe_json(response)
                if isinstance(payload, dict) and 'error' in payload:
                    if payload['error'] in ['daily_limit', 'api_download_limit_exceeded']:
                        raise DownloadLimitExceeded("Daily download limit exceeded")
                    elif payload['error'] == 'rate_limit':
                        if attempts < self.MAX_RETRY_ATTEMPTS:
                            logger.debug("API request rate limit hit, waiting and trying again.")
                            self._sleep_for_retry(response, default=15, label='Rate limit')
                            return self.checked(fn, is_retry=True, retry_attempt=retry_attempt,
                                                attempts=attempts + 1)
                        raise APIThrottled("API request limit hit")
                    elif payload['error'] == 'service_busy':
                        if retry_attempt < 5 and attempts < self.MAX_RETRY_ATTEMPTS:
                            logger.debug("API service is busy, waiting and trying again.")
                            self._sleep_for_retry(response, default=5, label='Service busy')
                            return self.checked(fn, is_retry=is_retry,
                                                retry_attempt=retry_attempt + 1,
                                                attempts=attempts + 1)
                        raise ProviderError("API service is busy")
                raise APIThrottled(f'Rate limited without a usable error field: {payload}')
            elif 400 <= status_code < 500:
                # A client error is about this one request (a rejected title, a
                # malformed parameter) and says nothing about provider health.
                payload = self._safe_json(response)
                message = payload.get('error') or payload.get('message') or f'HTTP {status_code}'
                raise SubdlRequestRejected(f'Request rejected ({status_code}): {message}')
            elif status_code != 200:
                payload = self._safe_json(response)
                message = payload.get('error') or payload.get('message') or ''
                logger.error(f'Unhandled API response {status_code}: {message}')
                raise ServiceUnavailable(f'subdl returned HTTP {status_code}')

        return response
