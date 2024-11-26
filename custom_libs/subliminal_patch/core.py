# coding=utf-8
import six
import json
import re
import os
import logging
import datetime
import socket
import traceback
import time
import operator
import unicodedata
import itertools
import rarfile
import requests

from os import scandir
from collections import defaultdict
from bs4 import UnicodeDammit
from babelfish import LanguageReverseError
from guessit.jsonutils import GuessitEncoder
from subliminal import refiner_manager
from concurrent.futures import as_completed

from .extensions import provider_registry
from .exceptions import MustGetBlacklisted
from .score import compute_score as default_compute_score
from subliminal.utils import hash_napiprojekt, hash_opensubtitles, hash_shooter, hash_thesubdb
from subliminal.video import VIDEO_EXTENSIONS, Video, Episode, Movie
from subliminal.core import guessit, ProviderPool, io, is_windows_special_path, \
    ThreadPoolExecutor, check_video

from subzero.language import Language, ENDSWITH_LANGUAGECODE_RE, FULL_LANGUAGE_LIST

logger = logging.getLogger(__name__)

# may be absolute or relative paths; set to selected options
CUSTOM_PATHS = []
INCLUDE_EXOTIC_SUBS = True

DOWNLOAD_TRIES = 3
DOWNLOAD_RETRY_SLEEP = 6

# fixme: this may be overkill
REMOVE_CRAP_FROM_FILENAME = re.compile(r"(?i)(?:([\s_-]+(?:obfuscated|scrambled|nzbgeek|chamele0n|buymore|xpost|postbot"
                                       r"|asrequested)(?:\[.+\])?)|([\s_-]\w{2,})(\[.+\]))(?=\.\w+$|$)")

SUBTITLE_EXTENSIONS = ('.srt', '.sub', '.smi', '.txt', '.ssa', '.ass', '.mpl', '.vtt')

_POOL_LIFETIME = datetime.timedelta(hours=12)

HI_REGEX_WITHOUT_PARENTHESIS = re.compile(r'[*¶♫♪].{3,}[*¶♫♪]|[\[\{].{3,}[\]\}](?<!{\\an\d})')
HI_REGEX_WITH_PARENTHESIS = re.compile(r'[*¶♫♪].{3,}[*¶♫♪]|[\[\(\{].{3,}[\]\)\}](?<!{\\an\d})')

HI_REGEX_PARENTHESIS_EXCLUDED_LANGUAGES = ['ara']


def parse_for_hi_regex(subtitle_text, alpha3_language):
    if alpha3_language in HI_REGEX_PARENTHESIS_EXCLUDED_LANGUAGES:
        return bool(re.search(HI_REGEX_WITHOUT_PARENTHESIS, subtitle_text))
    else:
        return bool(re.search(HI_REGEX_WITH_PARENTHESIS, subtitle_text))


def remove_crap_from_fn(fn):
    # in case of the second regex part, the legit release group name will be in group(2), if it's followed by [string]
    # otherwise replace fully, because the first part matched
    def repl(m):
        return m.group(2) if len(m.groups()) == 3 else ""

    return REMOVE_CRAP_FROM_FILENAME.sub(repl, fn)


def _nested_update(item, to_update):
    for k, v in to_update.items():
        if isinstance(v, dict):
            item[k] = _nested_update(item.get(k, {}), v)
        else:
            item[k] = v

    return item


class _ProviderConfigs(dict):
    def __init__(self, pool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pool = pool

    def update(self, items):
        updated = set()
        # Restart providers with new configs
        for key, val in items.items():
            # Don't restart providers that are not enabled
            if key not in self._pool.providers:
                continue

            # key: provider's name; val: config dict
            registered_val = self.get(key)

            if registered_val is None or registered_val == val:
                continue

            updated.add(key)

            # The new dict might be a partial dict
            registered_val.update(val)

            logger.debug("Config changed. Restarting provider: %s", key)
            try:
                provider = provider_registry[key](**registered_val)  # type: ignore
                provider.initialize()
            except Exception as error:
                self._pool.throttle_callback(key, error)
            else:
                self._pool.initialized_providers[key] = provider

        if updated:
            logger.debug("Providers with config updates: %s", updated)
        else:
            logger.debug("No provider config updates")

        _nested_update(self, items)

        return None


class _Banlist:
    def __init__(self, must_not_contain, must_contain):
        self.must_not_contain = must_not_contain
        self.must_contain = must_contain

    def is_valid(self, subtitle):
        if subtitle.release_info is None:
            return True

        if any([x for x in self.must_not_contain
                if re.search(x, subtitle.release_info, flags=re.IGNORECASE) is not None]):
            logger.info("Skipping subtitle because release name contains prohibited string: %s", subtitle)
            return False
        if any([x for x in self.must_contain
                if re.search(x, subtitle.release_info, flags=re.IGNORECASE) is None]):
            logger.info("Skipping subtitle because release name does not contains required string: %s", subtitle)
            return False

        return True


class _Blacklist(list):
    def is_valid(self, provider, subtitle):
        blacklisted = (str(provider), str(subtitle.id)) in self
        if blacklisted:
            logger.debug("Blacklisted subtitle: %s", subtitle)

        return not blacklisted


class _LanguageEquals(list):
    """ An optional config field for the pool. It will treat a couple of languages as equal for
    list-subtitles operations. It's optional; its methods won't do anything if an empy list
    is set.

    Example usage: [(language_instance, language_instance), ...]"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for item in self:
            if len(item) != 2 or not any(isinstance(i, Language) for i in item):
                raise ValueError(f"Not a valid equal tuple: {item}")

    def translate(self, items: set):
        translated = items.copy()

        for equals in self:
            from_, to_ = equals
            if to_ in items:
                logger.debug("Translating %r -> %r", to_, from_)
                translated.add(from_)

        if translated == items:
            logger.debug("Nothing to translate found")

        return translated or items

    def check_set(self, items: set):
        """ Check a set of languages. For example, if the set is {Language('es')} and one of the
        equals of the instance is (Language('es'), Language('es', 'MX')), the set will now have
        to {Language('es'), Language('es', 'MX')}.

        It will return a copy of the original set to avoid messing up outside its scope.

        Note that hearing_impaired and forced language attributes are not yet tested.
        """
        to_add = []
        for equals in self:
            from_, to_ = equals
            if from_ in items:
                logger.debug("Adding %r to %s item(s) set", to_, len(items))
                to_add.append(to_)

        new_items = items.copy()
        new_items.update(to_add)
        logger.debug("New set: %s items", len(new_items))
        return new_items

    def update_subtitle(self, subtitle):
        for equals in self:
            from_, to_ = equals
            if from_ == subtitle.language:
                logger.debug("Updating language for %r (to %r)", subtitle, to_)
                subtitle.language = to_
                break


class SZProviderPool(ProviderPool):
    def __init__(self, providers=None, provider_configs=None, blacklist=None, ban_list=None, throttle_callback=None,
                 pre_download_hook=None, post_download_hook=None, language_hook=None, language_equals=None):
        #: Name of providers to use
        self.providers = set(providers or [])

        #: Initialized providers
        self.initialized_providers = {}

        #: Discarded providers
        self.discarded_providers = set()

        self.blacklist = _Blacklist(blacklist or [])

        #: Should be a dict of 2 lists of strings
        self.ban_list = _Banlist(**(ban_list or {'must_contain': [], 'must_not_contain': []}))

        self.lang_equals = _LanguageEquals(language_equals or [])

        self.throttle_callback = throttle_callback

        self.pre_download_hook = pre_download_hook
        self.post_download_hook = post_download_hook
        self.language_hook = language_hook

        self._born = time.time()

        if not self.throttle_callback:
            self.throttle_callback = lambda x, y, ids=None, language=None: x

        #: Provider configuration
        self.provider_configs = _ProviderConfigs(self)
        self.provider_configs.update(provider_configs or {})

    def update(self, providers, provider_configs, blacklist, ban_list, language_equals=None):
        # Check if the pool was initialized enough hours ago
        self._check_lifetime()

        providers = set(providers or [])

        # Check if any new provider has been added
        updated = providers != self.providers or ban_list != self.ban_list
        removed_providers = set(sorted(self.providers - providers))

        logger.debug("Discarded providers: %s | New providers: %s", self.discarded_providers, providers)
        self.discarded_providers.difference_update(providers)
        logger.debug("Updated discarded providers: %s", self.discarded_providers)

        removed_providers.update(self.discarded_providers)

        logger.debug("Removed providers: %s", removed_providers)

        self.providers.difference_update(removed_providers)
        self.providers.update(list(providers))

        # Terminate and delete removed providers from instance
        for removed in removed_providers:
            logger.debug("Removing provider: %s", removed)
            try:
                del self[removed]
                # If the user has updated the providers but hasn't made any
                # subtitle searches yet, the removed provider won't be in the
                # self dictionary
            except KeyError:
                pass

        # self.provider_configs = provider_configs
        self.provider_configs.update(provider_configs)

        self.blacklist = _Blacklist(blacklist or [])
        self.ban_list = _Banlist(**ban_list or {'must_contain': [], 'must_not_contain': []})
        self.lang_equals = _LanguageEquals(language_equals or [])

        return updated

    def _check_lifetime(self):
        # This method is used to avoid possible memory leaks
        if abs(self._born - time.time()) > _POOL_LIFETIME.seconds:
            logger.info("%s elapsed. Terminating providers", _POOL_LIFETIME)
            self._born = time.time()
            self.terminate()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.terminate()

    def __getitem__(self, name):
        if name not in self.providers:
            raise KeyError
        if name not in self.initialized_providers:
            logger.info('Initializing provider %s', name)
            provider = provider_registry[name](**self.provider_configs.get(name, {}))
            provider.initialize()
            self.initialized_providers[name] = provider

        return self.initialized_providers[name]

    def __delitem__(self, name):
        if name not in self.initialized_providers:
            raise KeyError(name)

        try:
            logger.info('Terminating provider %s', name)
            self.initialized_providers[name].terminate()
        except (requests.Timeout, socket.timeout) as e:
            logger.error('Provider %r timed out, improperly terminated', name)
            self.throttle_callback(name, e)
        except Exception as e:
            logger.exception('Provider %r terminated unexpectedly', name)
            self.throttle_callback(name, e)

        del self.initialized_providers[name]

    def list_subtitles_provider(self, provider, video, languages):
        """List subtitles with a single provider.

        The video and languages are checked against the provider.

        patch: add traceback info

        :param str provider: name of the provider.
        :param video: video to list subtitles for.
        :type video: :class:`~subliminal.video.Video`
        :param languages: languages to search for.
        :type languages: set of :class:`~babelfish.language.Language`
        :return: found subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle` or None

        """
        logger.debug("Languages requested: %r", languages)

        if self.language_hook:
            languages_search_base = self.language_hook(provider)
        else:
            languages_search_base = languages

        # check video validity
        if not provider_registry[provider].check(video):
            logger.info('Skipping provider %r: not a valid video', provider)
            return []

        # check whether we want to search this provider for the languages
        use_languages = languages_search_base & languages
        if not use_languages:
            logger.info('Skipping provider %r: no language to search for (advanced: %r, requested: %r)', provider,
                        languages_search_base, languages)
            return []

        # check supported languages
        provider_languages = self.lang_equals.check_set(set(provider_registry[provider].languages)) & use_languages
        if not provider_languages:
            logger.info('Skipping provider %r: no language to search for', provider)
            return []

        # list subtitles
        results = []

        to_request = self.lang_equals.translate(provider_languages) & set(provider_registry[provider].languages)

        logger.info('Listing subtitles with provider %r and languages %r', provider, to_request)

        try:
            results = self[provider].list_subtitles(video, to_request)
            seen = []
            out = []
            for s in results:
                self.lang_equals.update_subtitle(s)

                if not self.blacklist.is_valid(provider, s):
                    continue

                if not self.ban_list.is_valid(s):
                    continue

                if s.id in seen:
                    continue

                s.radarrId = video.radarrId if hasattr(video, 'radarrId') else None
                s.sonarrSeriesId = video.sonarrSeriesId if hasattr(video, 'sonarrSeriesId') else None
                s.sonarrEpisodeId = video.sonarrEpisodeId if hasattr(video, 'sonarrEpisodeId') else None

                s.plex_media_fps = float(video.fps) if video.fps else None
                out.append(s)
                seen.append(s.id)

            return out

        except Exception as e:
            ids = {
                'radarrId': video.radarrId if hasattr(video, 'radarrId') else None,
                'sonarrSeriesId': video.sonarrSeriesId if hasattr(video, 'sonarrSeriesId') else None,
                'sonarrEpisodeId': video.sonarrEpisodeId if hasattr(video, 'sonarrEpisodeId') else None,
            }
            logger.exception('Unexpected error in provider %r: %s', provider, traceback.format_exc())
            self.throttle_callback(provider, e, ids=ids, language=list(languages)[0] if len(languages) else None)

    def list_subtitles(self, video, languages):
        """List subtitles.

        patch: handle LanguageReverseError

        :param video: video to list subtitles for.
        :type video: :class:`~subliminal.video.Video`
        :param languages: languages to search for.
        :type languages: set of :class:`~babelfish.language.Language`
        :return: found subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`

        """
        subtitles = []

        for name in self.providers:
            # check discarded providers
            if name in self.discarded_providers:
                logger.debug('Skipping discarded provider %r', name)
                continue

            # list subtitles
            try:
                provider_subtitles = self.list_subtitles_provider(name, video, languages)
            except LanguageReverseError:
                logger.exception("Unexpected language reverse error in %s, skipping. Error: %s", name,
                                 traceback.format_exc())
                continue

            if provider_subtitles is None:
                logger.info('Discarding provider %s', name)
                self.discarded_providers.add(name)
                continue

            # add the subtitles
            subtitles.extend(provider_subtitles)

        return subtitles

    def download_subtitle(self, subtitle):
        """Download `subtitle`'s :attr:`~subliminal.subtitle.Subtitle.content`.

        patch: add retry functionality

        :param subtitle: subtitle to download.
        :type subtitle: :class:`~subliminal.subtitle.Subtitle`
        :return: `True` if the subtitle has been successfully downloaded, `False` otherwise.
        :rtype: bool
        """
        # check discarded providers
        if subtitle.provider_name in self.discarded_providers:
            logger.warning('Provider %r is discarded', subtitle.provider_name)
            return False

        logger.info('Downloading subtitle %r', subtitle)
        tries = 0

        ids = {
            'radarrId': subtitle.radarrId if hasattr(subtitle, 'radarrId') else None,
            'sonarrSeriesId': subtitle.sonarrSeriesId if hasattr(subtitle, 'sonarrSeriesId') else None,
            'sonarrEpisodeId': subtitle.sonarrEpisodeId if hasattr(subtitle, 'sonarrEpisodeId') else None,
        }

        # retry downloading on failure until settings' download retry limit hit
        while True:
            tries += 1
            try:
                if self.pre_download_hook:
                    self.pre_download_hook(subtitle)

                self[subtitle.provider_name].download_subtitle(subtitle)
                if self.post_download_hook:
                    self.post_download_hook(subtitle)

                break
            except (requests.ConnectionError,
                    requests.exceptions.ProxyError,
                    requests.exceptions.SSLError,
                    requests.Timeout,
                    socket.timeout) as e:
                logger.error('Provider %r connection error', subtitle.provider_name)
                self.throttle_callback(subtitle.provider_name, e, ids=ids, language=subtitle.language)

            except (rarfile.BadRarFile, MustGetBlacklisted) as e:
                self.throttle_callback(subtitle.provider_name, e, ids=ids, language=subtitle.language)
                return False

            except Exception as e:
                logger.exception('Unexpected error in provider %r, Traceback: %s', subtitle.provider_name,
                                 traceback.format_exc())
                self.throttle_callback(subtitle.provider_name, e, ids=ids, language=subtitle.language)
                self.discarded_providers.add(subtitle.provider_name)
                return False

            if tries == DOWNLOAD_TRIES:
                self.discarded_providers.add(subtitle.provider_name)
                logger.error('Maximum retries reached for provider %r, discarding it', subtitle.provider_name)
                return False

            # don't hammer the provider
            logger.debug('Errors while downloading subtitle, retrying provider %r in %s seconds',
                         subtitle.provider_name, DOWNLOAD_RETRY_SLEEP)
            time.sleep(DOWNLOAD_RETRY_SLEEP)

        # check subtitle validity
        if not subtitle.is_valid():
            logger.error('Invalid subtitle')
            return False

        if not os.environ.get("SZ_KEEP_ENCODING", False):
            subtitle.normalize()

        return True

    def download_best_subtitles(self, subtitles, video, languages, min_score=0, hearing_impaired=False, only_one=False,
                                compute_score=None, use_original_format=False):
        """Download the best matching subtitles.

        patch:
            - hearing_impaired is now string
            - add .score to subtitle
            - move all languages check further to the top (still necessary?)

        :param subtitles: the subtitles to use.
        :type subtitles: list of :class:`~subliminal.subtitle.Subtitle`
        :param video: video to download subtitles for.
        :type video: :class:`~subliminal.video.Video`
        :param languages: languages to download.
        :type languages: set of :class:`~babelfish.language.Language`
        :param int min_score: minimum score for a subtitle to be downloaded.
        :param bool hearing_impaired: hearing impaired preference.
        :param bool only_one: download only one subtitle, not one per language.
        :param compute_score: function that takes `subtitle` and `video` as positional arguments,
            `hearing_impaired` as keyword argument and returns the score.
        :param bool use_original_format: preserve original subtitles format
        :return: downloaded subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`

        """
        compute_score = compute_score or default_compute_score
        use_hearing_impaired = hearing_impaired in ("prefer", "force HI")

        is_episode = isinstance(video, Episode)
        max_score = sum(val for key, val in compute_score._scores['episode' if is_episode else 'movie'].items() if key != "hash")

        # sort subtitles by score
        unsorted_subtitles = []

        for s in subtitles:
            # get the matches
            if s.language.basename not in [x.basename for x in languages]:
                logger.debug("%r: Skipping, language not searched for", s)
                continue

            try:
                matches = s.get_matches(video)
            except AttributeError:
                logger.error("%r: Match computation failed: %s", s, traceback.format_exc())
                continue

            orig_matches = matches.copy()

            logger.debug('%r: Found matches %r', s, matches)
            score, score_without_hash = compute_score(matches, s, video, use_hearing_impaired)
            unsorted_subtitles.append(
                (s, score, score_without_hash, matches, orig_matches))

        # sort subtitles by score
        scored_subtitles = sorted(unsorted_subtitles, key=operator.itemgetter(1, 2), reverse=True)

        # download best subtitles, falling back on the next on error
        downloaded_subtitles = []
        for subtitle, score, score_without_hash, matches, orig_matches in scored_subtitles:
            # check score
            if score < min_score:
                min_score_in_percent = round(min_score * 100 / max_score, 2) if min_score > 0 else 0
                logger.info('%r: Score %d is below min_score: %d out of %d (or %r%%)',
                            subtitle, score, min_score, max_score, min_score_in_percent)
                break

            # stop when all languages are downloaded
            if set(str(s.language) for s in downloaded_subtitles) == languages:
                logger.debug('All languages downloaded')
                break

            # check downloaded languages
            if subtitle.language in set(str(s.language) for s in downloaded_subtitles):
                logger.debug('%r: Skipping subtitle: already downloaded', subtitle.language)
                continue

            # bail out if hearing_impaired was wrong
            if subtitle.hearing_impaired_verifiable and "hearing_impaired" not in matches and \
                    hearing_impaired in ("force HI", "force non-HI"):
                logger.debug('%r: Skipping subtitle with score %d because hearing-impaired set to %s', subtitle,
                             score, hearing_impaired)
                continue

            if is_episode:
                can_verify_series = True
                if not subtitle.hash_verifiable and "hash" in matches:
                    can_verify_series = False

                matches_series = False
                if {"season", "episode"}.issubset(orig_matches) and \
                        ("series" in orig_matches or "imdb_id" in orig_matches):
                    matches_series = True

                if can_verify_series and not matches_series:
                    logger.debug("%r: Skipping subtitle with score %d, because it doesn't match our series/episode",
                                 subtitle, score)
                    continue

            # make sure to preserve original subtitles format if requested
            subtitle.use_original_format = use_original_format

            # download
            logger.debug("%r: Trying to download subtitle with matches %s, score: %s; release(s): %s", subtitle,
                         matches, score, subtitle.release_info)
            if self.download_subtitle(subtitle):
                subtitle.score = score
                downloaded_subtitles.append(subtitle)

            # stop if only one subtitle is requested
            if only_one:
                logger.debug('Only one subtitle downloaded')
                break

        return downloaded_subtitles

    def list_supported_languages(self):
        """List supported languages.

        :return: languages supported by the providers.
        :rtype: list of dicts

        """
        languages = []

        for name in self.providers:
            # list supported languages for a single provider
            try:
                provider_languages = self[name].languages
            except AttributeError:
                logger.exception(f"{name} provider doesn't have a languages attribute")
                continue

            if provider_languages is None:
                logger.info(f"Skipping provider {name} because it doesn't support any languages.")
                continue

            # add the languages for this provider
            languages.append({'provider': name, 'languages': self.lang_equals.check_set(set(provider_languages))})

        return languages

    def list_supported_video_types(self):
        """List supported video types.

        :return: video types supported by the providers.
        :rtype: tuple of video types

        """
        video_types = []

        for name in self.providers:
            # list supported video types for a single provider
            try:
                provider_video_type = self[name].video_types
            except AttributeError:
                logger.exception(f"{name} provider doesn't have a video_types method")
                continue

            if provider_video_type is None:
                logger.info(f"Skipping provider {name} because it doesn't support any video type.")
                continue

            # add the video types for this provider
            video_types.append({'provider': name, 'video_types': provider_video_type})

        return video_types

    def __repr__(self):
        return (
            f"{self.__class__.__name__} [{len(self.providers)} providers ({len(self.initialized_providers)} "
            f"initialized; {len(self.discarded_providers)} discarded)]"
        )


class SZAsyncProviderPool(SZProviderPool):
    """Subclass of :class:`ProviderPool` with asynchronous support for :meth:`~ProviderPool.list_subtitles`.

    :param int max_workers: maximum number of threads to use. If `None`, :attr:`max_workers` will be set
        to the number of :attr:`~ProviderPool.providers`.

    """

    def __init__(self, max_workers=None, *args, **kwargs):
        super(SZAsyncProviderPool, self).__init__(*args, **kwargs)

        #: Maximum number of threads to use
        self._max_workers_set = max_workers is not None
        self.max_workers = (max_workers or len(self.providers)) or 1
        logger.info("Using %d threads for %d providers (%s)", self.max_workers, len(self.providers), self.providers)

    def update(self, *args, **kwargs):
        updated = super().update(*args, **kwargs)

        if (len(self.providers) and not self._max_workers_set) and len(self.providers) != self.max_workers:
            logger.debug("This pool will use %d threads from now on", len(self.providers))
            self.max_workers = len(self.providers)

        return updated

    def list_subtitles_provider(self, provider, video, languages):
        # list subtitles
        provider_subtitles = None
        try:
            provider_subtitles = super(SZAsyncProviderPool, self).list_subtitles_provider(provider, video, languages)
        except LanguageReverseError:
            logger.exception("Unexpected language reverse error in %s, skipping. Error: %s", provider,
                             traceback.format_exc())

        return provider, provider_subtitles

    def list_subtitles(self, video, languages, blacklist=None, ban_list=None):
        if is_windows_special_path:
            return super(SZAsyncProviderPool, self).list_subtitles(video, languages)

        subtitles = []

        with ThreadPoolExecutor(self.max_workers) as executor:
            for provider, provider_subtitles in executor.map(self.list_subtitles_provider, self.providers,
                                                             itertools.repeat(video, len(self.providers)),
                                                             itertools.repeat(languages, len(self.providers))):
                # discard provider that failed
                if provider_subtitles is None:
                    logger.info('Discarding provider %s', provider)
                    self.discarded_providers.add(provider)
                    continue

                # add subtitles
                subtitles.extend(provider_subtitles)

        return subtitles

    def list_supported_languages(self):
        """List supported languages asynchronously.

        :return: languages supported by the providers.
        :rtype: list of dicts

        """
        languages = []

        def get_providers_languages(provider_name):
            provider_languages = None
            try:
                provider_languages = {'provider': provider_name, 'languages': self[provider_name].languages}
            except AttributeError:
                logger.exception(f"{provider_name} provider doesn't have a languages attribute")

            return provider_languages

        with ThreadPoolExecutor(self.max_workers) as executor:
            for future in as_completed([executor.submit(get_providers_languages, x) for x in self.providers]):
                provider_languages = future.result()
                if provider_languages is None:
                    continue

                # add the languages for this provider
                languages.append(provider_languages)

        return languages

    def list_supported_video_types(self):
        """List supported video types asynchronously.

        :return: video types supported by the providers.
        :rtype: tuple of video types

        """
        video_types = []

        def get_providers_video_types(provider_name):
            provider_video_types = None
            try:
                provider_video_types = {'provider': provider_name,
                                        'video_types': self[provider_name].video_types}
            except AttributeError:
                logger.exception(f"{provider_name} provider doesn't have a video_types attribute")

            return provider_video_types

        with ThreadPoolExecutor(self.max_workers) as executor:
            for future in as_completed([executor.submit(get_providers_video_types, x) for x in self.providers]):
                provider_video_types = future.result()
                if provider_video_types is None:
                    continue

                # add the languages for this provider
                video_types.append(provider_video_types)

        return video_types


if is_windows_special_path:
    SZAsyncProviderPool = SZProviderPool


def scan_video(path, dont_use_actual_file=False, hints=None, providers=None, skip_hashing=False, hash_from=None):
    """Scan a video from a `path`.

    patch:
        - allow passing of hints/options to guessit
        - allow dry-run with dont_use_actual_file
        - add crap removal (obfuscated/scrambled)
        - trust plex's movie name

    :param str path: existing path to the video.
    :return: the scanned video.
    :rtype: :class:`~subliminal.video.Video`

    """
    hints = hints or {}

    # check for non-existing path
    if not dont_use_actual_file and not os.path.exists(path):
        raise ValueError('Path does not exist')

    # check video extension
    if not path.lower().endswith(VIDEO_EXTENSIONS):
        raise ValueError('%r is not a valid video extension' % os.path.splitext(path)[1])

    dirpath, filename = os.path.split(path)
    logger.info('Determining basic video properties for %r in %r', filename, dirpath)

    hints["single_value"] = True
    #    if "title" in hints:
    #        hints["expected_title"] = [hints["title"]]

    guessed_result = guessit(path, options=hints)

    logger.debug('GuessIt found: %s', json.dumps(guessed_result, cls=GuessitEncoder, indent=4, ensure_ascii=False))
    video = Video.fromguess(path, guessed_result)
    video.hints = hints  # ?

    if dont_use_actual_file and not hash_from:
        return video

    # if all providers are throttled, skip hashing
    if not providers:
        skip_hashing = True

    # size and hashes
    if not skip_hashing:
        hash_path = hash_from or path
        video.size = os.path.getsize(hash_path)
        if video.size > 10485760:
            logger.debug('Size is %d', video.size)
            osub_hash = None

            if "bsplayer" in providers:
                video.hashes['bsplayer'] = osub_hash = hash_opensubtitles(hash_path)

            if "opensubtitles" in providers:
                video.hashes['opensubtitles'] = osub_hash = osub_hash or hash_opensubtitles(hash_path)

            if "opensubtitlescom" in providers:
                video.hashes['opensubtitlescom'] = osub_hash = osub_hash or hash_opensubtitles(hash_path)

            if "shooter" in providers:
                video.hashes['shooter'] = hash_shooter(hash_path)

            if "thesubdb" in providers:
                video.hashes['thesubdb'] = hash_thesubdb(hash_path)

            if "napiprojekt" in providers:
                try:
                    video.hashes['napiprojekt'] = hash_napiprojekt(hash_path)
                except MemoryError:
                    logger.warning(u"Couldn't compute napiprojekt hash for %s", hash_path)

            if "napisy24" in providers:
                # Napisy24 uses the same hash as opensubtitles
                video.hashes['napisy24'] = osub_hash or hash_opensubtitles(hash_path)

            logger.debug('Computed hashes %r', video.hashes)
        else:
            logger.warning('Size is lower than 10MB: hashes not computed')

    return video


def _search_external_subtitles(path, languages=None, only_one=False, match_strictness="strict"):
    dirpath, filename = os.path.split(path)
    dirpath = dirpath or '.'
    fn_no_ext, fileext = os.path.splitext(filename)
    fn_no_ext_lower = fn_no_ext.lower() # unicodedata.normalize('NFC', fn_no_ext.lower())
    subtitles = {}

    for entry in scandir(dirpath):
        if not entry.is_file(follow_symlinks=False):
            continue

        p = entry.name # unicodedata.normalize('NFC', entry.name)

        # keep only valid subtitle filenames
        if not p.lower().endswith(SUBTITLE_EXTENSIONS):
            continue

        # not p.lower().startswith(fileroot.lower()) or not

        p_root, p_ext = os.path.splitext(p)
        if not INCLUDE_EXOTIC_SUBS and p_ext not in (".srt", ".ass", ".ssa", ".vtt"):
            continue

        if p_root.lower() == fn_no_ext_lower:
            # skip check for language code if the subtitle file name is the same as the video name
            subtitles[p] = None
            continue

        # extract potential forced/normal/default/hi tag
        # fixme: duplicate from subtitlehelpers
        split_tag = p_root.rsplit('.', 1)
        adv_tag = None
        if len(split_tag) > 1:
            adv_tag = split_tag[1].lower()
            if adv_tag in ['forced', 'normal', 'default', 'embedded', 'embedded-forced', 'custom', 'hi', 'cc', 'sdh']:
                p_root = split_tag[0]

        forced = False
        if adv_tag:
            forced = "forced" in adv_tag

        hi = False
        if adv_tag:
            hi_tag = ["hi", "cc", "sdh"]
            hi = any(i for i in hi_tag if i in adv_tag)

        # add simplified/traditional chinese detection
        simplified_chinese = ["chs", "sc", "zhs", "hans", "zh-hans", "gb", "简", "简中", "简体", "简体中文", "中英双语",
                              "中日双语", "中法双语", "简体&英文"]
        traditional_chinese = ["cht", "tc", "zht", "hant", "zh-hant", "big5", "繁", "繁中", "繁体", "繁體", "繁体中文",
                               "繁體中文", "正體中文", "中英雙語", "中日雙語", "中法雙語", "繁体&英文"]
        p_root = p_root.replace('zh-TW', 'zht')

        # remove possible language code for matching
        p_root_bare = ENDSWITH_LANGUAGECODE_RE.sub(
            lambda m: "" if str(m.group(1)).lower() in FULL_LANGUAGE_LIST else m.group(0), p_root)

        p_root_lower = p_root_bare.lower()
        # comparing to both unicode normalization forms to prevent broking stuff and improve indexing on some platforms.
        filename_matches = fn_no_ext_lower in [p_root_lower, unicodedata.normalize('NFC', p_root_lower)]
        filename_contains = p_root_lower in fn_no_ext_lower

        if not filename_matches:
            if match_strictness == "strict" or (match_strictness == "loose" and not filename_contains):
                continue

        language = None

        # extract the potential language code
        try:
            language_code = p_root.rsplit(".", 1)[1].replace('_', '-')
            try:
                language = Language.fromietf(language_code)
                language.forced = forced
                language.hi = hi
            except (ValueError, LanguageReverseError):
                # add simplified/traditional chinese detection
                if any(ext in str(language_code) for ext in simplified_chinese):
                    language = Language.fromietf('zh')
                    language.forced = forced
                    language.hi = hi
                elif any(ext in str(language_code) for ext in traditional_chinese):
                    language = Language.fromietf('zh')
                    language.forced = forced
                    language.hi = hi
                else:
                    logger.error('Cannot parse language code %r', language_code)
                    language_code = None
        except IndexError:
            language_code = None

        if not language and not language_code and only_one:
            language = Language.rebuild(list(languages)[0], forced=forced, hi=hi)

        subtitles[p] = language

    logger.debug('Found subtitles %r', subtitles)

    return subtitles


def search_external_subtitles(path, languages=None, only_one=False, match_strictness="strict"):
    """
    wrap original search_external_subtitles function to search multiple paths for one given video
    # todo: cleanup and merge with _search_external_subtitles
    """
    video_path, video_filename = os.path.split(path)
    subtitles = {}
    for folder_or_subfolder in [video_path] + CUSTOM_PATHS:
        # folder_or_subfolder may be a relative path or an absolute one
        try:
            abspath = six.text_type(os.path.abspath(
                os.path.join(*[video_path if not os.path.isabs(folder_or_subfolder) else "", folder_or_subfolder,
                               video_filename])))
        except Exception as e:
            logger.error("skipping path %s because of %s", repr(folder_or_subfolder), e)
            continue
        logger.debug("external subs: scanning path %s", abspath)

        if os.path.isdir(os.path.dirname(abspath)):
            subtitles.update(_search_external_subtitles(abspath, languages=languages, only_one=only_one,
                                                        match_strictness=match_strictness))
    logger.debug("external subs: found %s", subtitles)
    return subtitles


def list_all_subtitles(videos, languages, **kwargs):
    """List all available subtitles.

    patch: remove video check, it has been done before

    The `videos` must pass the `languages` check of :func:`check_video`.

    All other parameters are passed onwards to the :class:`ProviderPool` constructor.

    :param videos: videos to list subtitles for.
    :type videos: set of :class:`~subliminal.video.Video`
    :param languages: languages to search for.
    :type languages: set of :class:`~babelfish.language.Language`
    :return: found subtitles per video.
    :rtype: dict of :class:`~subliminal.video.Video` to list of :class:`~subliminal.subtitle.Subtitle`

    """
    listed_subtitles = defaultdict(list)

    # return immediatly if no video passed the checks
    if not videos:
        return listed_subtitles

    # list subtitles
    with SZProviderPool(**kwargs) as pool:
        for video in videos:
            logger.info('Listing subtitles for %r', video)
            subtitles = pool.list_subtitles(video, languages - video.subtitle_languages)
            listed_subtitles[video].extend(subtitles)
            logger.info('Found %d subtitle(s)', len(subtitles))

    return listed_subtitles


def list_supported_languages(pool_class, **kwargs):
    with pool_class(**kwargs) as pool:
        return pool.list_supported_languages()


def list_supported_video_types(pool_class, **kwargs):
    with pool_class(**kwargs) as pool:
        return pool.list_supported_video_types()


def download_subtitles(subtitles, pool_class=ProviderPool, **kwargs):
    r"""Download :attr:`~subliminal.subtitle.Subtitle.content` of `subtitles`.

    :param subtitles: subtitles to download.
    :type subtitles: list of :class:`~subliminal.subtitle.Subtitle`
    :param pool_class: class to use as provider pool.
    :type pool_class: :class:`ProviderPool`, :class:`AsyncProviderPool` or similar
    :param \*\*kwargs: additional parameters for the provided `pool_class` constructor.

    """
    with pool_class(**kwargs) as pool:
        for subtitle in subtitles:
            logger.info('Downloading subtitle %r with score %s', subtitle, subtitle.score)
            pool.download_subtitle(subtitle)


def download_best_subtitles(videos, languages, min_score=0, hearing_impaired=False, only_one=False, compute_score=None,
                            pool_class=ProviderPool, throttle_time=0, **kwargs):
    r"""List and download the best matching subtitles.

    The `videos` must pass the `languages` and `undefined` (`only_one`) checks of :func:`check_video`.

    :param videos: videos to download subtitles for.
    :type videos: set of :class:`~subliminal.video.Video`
    :param languages: languages to download.
    :type languages: set of :class:`~babelfish.language.Language`
    :param int min_score: minimum score for a subtitle to be downloaded.
    :param bool hearing_impaired: hearing impaired preference.
    :param bool only_one: download only one subtitle, not one per language.
    :param compute_score: function that takes `subtitle` and `video` as positional arguments,
        `hearing_impaired` as keyword argument and returns the score.
    :param pool_class: class to use as provider pool.
    :type pool_class: :class:`ProviderPool`, :class:`AsyncProviderPool` or similar
    :param \*\*kwargs: additional parameters for the provided `pool_class` constructor.
    :return: downloaded subtitles per video.
    :rtype: dict of :class:`~subliminal.video.Video` to list of :class:`~subliminal.subtitle.Subtitle`

    """
    downloaded_subtitles = defaultdict(list)

    # check videos
    checked_videos = []
    for video in videos:
        if not check_video(video, languages=languages, undefined=only_one):
            logger.info('Skipping video %r', video)
            continue
        checked_videos.append(video)

    # return immediately if no video passed the checks
    if not checked_videos:
        return downloaded_subtitles

    got_multiple = len(checked_videos) > 1

    # download best subtitles
    with pool_class(**kwargs) as pool:
        for video in checked_videos:
            logger.info('Downloading best subtitles for %r', video)
            subtitles = pool.download_best_subtitles(pool.list_subtitles(video, languages - video.subtitle_languages),
                                                     video, languages, min_score=min_score,
                                                     hearing_impaired=hearing_impaired, only_one=only_one,
                                                     compute_score=compute_score)
            logger.info('Downloaded %d subtitle(s)', len(subtitles))
            downloaded_subtitles[video].extend(subtitles)

            if got_multiple and throttle_time:
                logger.debug("Waiting %ss before continuing ...", throttle_time)
                time.sleep(throttle_time)

    return downloaded_subtitles


def get_subtitle_path(video_path, language=None, extension='.srt', forced_tag=False, hi_tag=False, tags=None):
    """Get the subtitle path using the `video_path` and `language`.

    :param str video_path: path to the video.
    :param language: language of the subtitle to put in the path.
    :type language: :class:`~babelfish.language.Language`
    :param str extension: extension of the subtitle.
    :param bool forced_tag: is the subtitles forced/foreign?
    :param bool hi_tag: is the subtitles hearing-impaired?
    :param list tags: list of custom tags
    :return: path of the subtitle.
    :rtype: str

    """
    subtitle_root = os.path.splitext(video_path)[0]
    tags = tags or []
    hi_extension = os.environ.get("SZ_HI_EXTENSION", "hi")

    if forced_tag:
        tags.append("forced")

    elif hi_tag:
        tags.append(hi_extension)

    if language:
        subtitle_root += '.' + str(language.basename)

    if tags:
        subtitle_root += ".%s" % "-".join(tags)

    return subtitle_root + extension


def save_subtitles(file_path, subtitles, single=False, directory=None, chmod=None, formats=("srt",),
                   tags=None, path_decoder=None, debug_mods=False):
    """Save subtitles on filesystem.

    Subtitles are saved in the order of the list. If a subtitle with a language has already been saved, other subtitles
    with the same language are silently ignored.

    The extension used is `.lang.srt` by default or `.srt` is `single` is `True`, with `lang` being the IETF code for
    the :attr:`~subliminal.subtitle.Subtitle.language` of the subtitle.

    :param file_path: video file path
    :param formats: list of "srt" and "vtt"
    :param subtitles: subtitles to save.
    :type subtitles: list of :class:`~subliminal.subtitle.Subtitle`
    :param bool single: save a single subtitle, default is to save one subtitle per language.
    :param str directory: path to directory where to save the subtitles, default is next to the video.
    :return: the saved subtitles
    :rtype: list of :class:`~subliminal.subtitle.Subtitle`

    patch: unicode path problems
    """

    logger.debug("Subtitle formats requested: %r", formats)

    saved_subtitles = []
    for subtitle in subtitles:
        # check if HI mods will be used to get the proper name for the subtitles file
        must_remove_hi = 'remove_HI' in subtitle.mods

        # check content
        if subtitle.content is None or subtitle.text is None:
            logger.error('Skipping subtitle %r: no content', subtitle)
            continue

        # check language
        if subtitle.language in set(s.language.basename for s in saved_subtitles):
            logger.debug('Skipping subtitle %r: language already saved', subtitle)
            continue

        # create subtitle path
        if (subtitle.text and subtitle.format == 'srt' and (hasattr(subtitle.language, 'hi') and
                                                            not subtitle.language.hi) and
                parse_for_hi_regex(subtitle_text=subtitle.text, alpha3_language=subtitle.language.alpha3 if
                                   (hasattr(subtitle, 'language') and hasattr(subtitle.language, 'alpha3')) else None)):
            subtitle.language.hi = True
        subtitle_path = get_subtitle_path(file_path, None if single else subtitle.language,
                                          forced_tag=subtitle.language.forced,
                                          hi_tag=False if must_remove_hi else subtitle.language.hi, tags=tags)
        if directory is not None:
            subtitle_path = os.path.join(directory, os.path.split(subtitle_path)[1])

        if path_decoder:
            subtitle_path = path_decoder(subtitle_path)

        # force unicode
        subtitle_path = UnicodeDammit(subtitle_path).unicode_markup

        subtitle.storage_path = subtitle_path

        for format in formats:
            if format != "srt":
                subtitle_path = os.path.splitext(subtitle_path)[0] + (u".%s" % format)

            logger.debug(u"Saving %r to %r", subtitle, subtitle_path)
            content = subtitle.get_modified_content(format=format, debug=debug_mods)
            if content:
                if os.path.exists(subtitle_path):
                    os.remove(subtitle_path)

                with open(subtitle_path, 'wb') as f:
                    f.write(content)
                subtitle.storage_path = subtitle_path
            else:
                logger.error(u"Something went wrong when getting modified subtitle for %s", subtitle)

        # change chmod if requested
        if chmod:
            os.chmod(subtitle_path, chmod)

        saved_subtitles.append(subtitle)

        # check single
        if single:
            break

    return saved_subtitles


def refine(video, episode_refiners=None, movie_refiners=None, **kwargs):
    r"""Refine a video using :ref:`refiners`.

    patch: add traceback logging

    .. note::

        Exceptions raised in refiners are silently passed and logged.

    :param video: the video to refine.
    :type video: :class:`~subliminal.video.Video`
    :param tuple episode_refiners: refiners to use for episodes.
    :param tuple movie_refiners: refiners to use for movies.
    :param \*\*kwargs: additional parameters for the :func:`~subliminal.refiners.refine` functions.

    """
    refiners = ()
    if isinstance(video, Episode):
        refiners = episode_refiners or ('metadata', 'tvdb', 'omdb')
    elif isinstance(video, Movie):
        refiners = movie_refiners or ('metadata', 'omdb')
    for refiner in refiners:
        logger.info('Refining video with %s', refiner)
        try:
            refiner_manager[refiner].plugin(video, **kwargs)
        except:
            logger.error('Failed to refine video: %s', traceback.format_exc())
