# coding=utf-8
import codecs
import json
import re
import os
import logging
import socket
import traceback
import time
import operator

import itertools
from httplib import ResponseNotReady

import rarfile
import requests

from collections import defaultdict
from bs4 import UnicodeDammit
from babelfish import LanguageReverseError
from guessit.jsonutils import GuessitEncoder
from subliminal import ProviderError, refiner_manager

from extensions import provider_registry
from subliminal.exceptions import ServiceUnavailable, DownloadLimitExceeded
from subliminal.score import compute_score as default_compute_score
from subliminal.utils import hash_napiprojekt, hash_opensubtitles, hash_shooter, hash_thesubdb
from subliminal.video import VIDEO_EXTENSIONS, Video, Episode, Movie
from subliminal.core import guessit, ProviderPool, io, is_windows_special_path, \
    ThreadPoolExecutor, check_video
from subliminal_patch.exceptions import TooManyRequests, APIThrottled

from subzero.language import Language, ENDSWITH_LANGUAGECODE_RE
from scandir import scandir, scandir_generic as _scandir_generic

logger = logging.getLogger(__name__)

# may be absolute or relative paths; set to selected options
CUSTOM_PATHS = []
INCLUDE_EXOTIC_SUBS = True

DOWNLOAD_TRIES = 0
DOWNLOAD_RETRY_SLEEP = 6

# fixme: this may be overkill
REMOVE_CRAP_FROM_FILENAME = re.compile(r"(?i)(?:([\s_-]+(?:obfuscated|scrambled|nzbgeek|chamele0n|buymore|xpost|postbot"
                                       r"|asrequested)(?:\[.+\])?)|([\s_-]\w{2,})(\[.+\]))(?=\.\w+$|$)")

SUBTITLE_EXTENSIONS = ('.srt', '.sub', '.smi', '.txt', '.ssa', '.ass', '.mpl', '.vtt')


def remove_crap_from_fn(fn):
    # in case of the second regex part, the legit release group name will be in group(2), if it's followed by [string]
    # otherwise replace fully, because the first part matched
    def repl(m):
        return m.group(2) if len(m.groups()) == 3 else ""

    return REMOVE_CRAP_FROM_FILENAME.sub(repl, fn)


class SZProviderPool(ProviderPool):
    def __init__(self, providers=None, provider_configs=None, blacklist=None, throttle_callback=None,
                 pre_download_hook=None, post_download_hook=None, language_hook=None):
        #: Name of providers to use
        self.providers = providers

        #: Provider configuration
        self.provider_configs = provider_configs or {}

        #: Initialized providers
        self.initialized_providers = {}

        #: Discarded providers
        self.discarded_providers = set()

        self.blacklist = blacklist or []

        self.throttle_callback = throttle_callback

        self.pre_download_hook = pre_download_hook
        self.post_download_hook = post_download_hook
        self.language_hook = language_hook

        if not self.throttle_callback:
            self.throttle_callback = lambda x, y: x

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
        except (requests.Timeout, socket.timeout):
            logger.error('Provider %r timed out, improperly terminated', name)
        except:
            logger.exception('Provider %r terminated unexpectedly', name)

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
        provider_languages = provider_registry[provider].languages & use_languages
        if not provider_languages:
            logger.info('Skipping provider %r: no language to search for', provider)
            return []

        # list subtitles
        logger.info('Listing subtitles with provider %r and languages %r', provider, provider_languages)
        results = []
        try:
            try:
                results = self[provider].list_subtitles(video, provider_languages)
            except ResponseNotReady:
                logger.error('Provider %r response error, reinitializing', provider)
                try:
                    self[provider].terminate()
                    self[provider].initialize()
                    results = self[provider].list_subtitles(video, provider_languages)
                except:
                    logger.error('Provider %r reinitialization error: %s', provider, traceback.format_exc())

            seen = []
            out = []
            for s in results:
                if (str(provider), str(s.id)) in self.blacklist:
                    logger.info("Skipping blacklisted subtitle: %s", s)
                    continue
                if s.id in seen:
                    continue
                s.plex_media_fps = float(video.fps) if video.fps else None
                out.append(s)
                seen.append(s.id)

            return out

        except (requests.Timeout, socket.timeout):
            logger.error('Provider %r timed out', provider)

        except Exception as e:
            logger.exception('Unexpected error in provider %r: %s', provider, traceback.format_exc())
            self.throttle_callback(provider, e)

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
                    socket.timeout):
                logger.error('Provider %r connection error', subtitle.provider_name)

            except ResponseNotReady:
                logger.error('Provider %r response error, reinitializing', subtitle.provider_name)
                try:
                    self[subtitle.provider_name].terminate()
                    self[subtitle.provider_name].initialize()
                except:
                    logger.error('Provider %r reinitialization error: %s', subtitle.provider_name,
                                 traceback.format_exc())

            except rarfile.BadRarFile:
                logger.error('Malformed RAR file from provider %r, skipping subtitle.', subtitle.provider_name)
                logger.debug("RAR Traceback: %s", traceback.format_exc())
                return False

            except Exception as e:
                logger.exception('Unexpected error in provider %r, Traceback: %s', subtitle.provider_name,
                                 traceback.format_exc())
                self.throttle_callback(subtitle.provider_name, e)
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
                                compute_score=None):
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
        :return: downloaded subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`

        """
        compute_score = compute_score or default_compute_score
        use_hearing_impaired = hearing_impaired in ("prefer", "force HI")

        is_episode = isinstance(video, Episode)

        # sort subtitles by score
        unsorted_subtitles = []

        for s in subtitles:
            # get the matches
            if s.language not in languages:
                logger.debug("%r: Skipping, language not searched for", s)
                continue

            try:
                matches = s.get_matches(video)
            except AttributeError:
                logger.error("%r: Match computation failed: %s", s, traceback.format_exc())
                continue

            orig_matches = matches.copy()

            logger.debug('%r: Found matches %r', s, matches)
            unsorted_subtitles.append(
                (s, compute_score(matches, s, video, hearing_impaired=use_hearing_impaired), matches, orig_matches))

        # sort subtitles by score
        scored_subtitles = sorted(unsorted_subtitles, key=operator.itemgetter(1), reverse=True)

        # download best subtitles, falling back on the next on error
        downloaded_subtitles = []
        for subtitle, score, matches, orig_matches in scored_subtitles:
            # check score
            if score < min_score:
                logger.info('%r: Score %d is below min_score (%d)', subtitle, score, min_score)
                break

            # stop when all languages are downloaded
            if set(s.language for s in downloaded_subtitles) == languages:
                logger.debug('All languages downloaded')
                break

            # check downloaded languages
            if subtitle.language in set(s.language for s in downloaded_subtitles):
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

            # download
            logger.debug("%r: Trying to download subtitle with matches %s, score: %s; release(s): %s", subtitle, matches,
                         score, subtitle.release_info)
            if self.download_subtitle(subtitle):
                subtitle.score = score
                downloaded_subtitles.append(subtitle)

            # stop if only one subtitle is requested
            if only_one:
                logger.debug('Only one subtitle downloaded')
                break

        return downloaded_subtitles


class SZAsyncProviderPool(SZProviderPool):
    """Subclass of :class:`ProviderPool` with asynchronous support for :meth:`~ProviderPool.list_subtitles`.

    :param int max_workers: maximum number of threads to use. If `None`, :attr:`max_workers` will be set
        to the number of :attr:`~ProviderPool.providers`.

    """
    def __init__(self, max_workers=None, *args, **kwargs):
        super(SZAsyncProviderPool, self).__init__(*args, **kwargs)

        #: Maximum number of threads to use
        self.max_workers = max_workers or len(self.providers)
        logger.info("Using %d threads for %d providers (%s)", self.max_workers, len(self.providers), self.providers)

    def list_subtitles_provider(self, provider, video, languages):
        # list subtitles
        provider_subtitles = None
        try:
            provider_subtitles = super(SZAsyncProviderPool, self).list_subtitles_provider(provider, video, languages)
        except LanguageReverseError:
            logger.exception("Unexpected language reverse error in %s, skipping. Error: %s", provider,
                             traceback.format_exc())

        return provider, provider_subtitles

    def list_subtitles(self, video, languages, blacklist=None):
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
    video_type = hints.get("type")

    # check for non-existing path
    if not dont_use_actual_file and not os.path.exists(path):
        raise ValueError('Path does not exist')

    # check video extension
    if not path.lower().endswith(VIDEO_EXTENSIONS):
        raise ValueError('%r is not a valid video extension' % os.path.splitext(path)[1])

    dirpath, filename = os.path.split(path)
    logger.info('Determining basic video properties for %r in %r', filename, dirpath)

    # hint guessit the filename itself and its 2 parent directories if we're an episode (most likely
    # Series name/Season/filename), else only one
    split_path = os.path.normpath(path).split(os.path.sep)[-3 if video_type == "episode" else -2:]

    # remove crap from folder names
    if video_type == "episode":
        if len(split_path) > 2:
            split_path[-3] = remove_crap_from_fn(split_path[-3])
    else:
        if len(split_path) > 1:
            split_path[-2] = remove_crap_from_fn(split_path[-2])

    guess_from = os.path.join(*split_path)

    # remove crap from file name
    guess_from = remove_crap_from_fn(guess_from)

    # guess
    hints["single_value"] = True
    if "title" in hints:
        hints["expected_title"] = [hints["title"]]

    guessed_result = guessit(guess_from, options=hints)

    logger.debug('GuessIt found: %s', json.dumps(guessed_result, cls=GuessitEncoder, indent=4, ensure_ascii=False))
    video = Video.fromguess(path, guessed_result)
    video.hints = hints

    # get possibly alternative title from the filename itself
    alt_guess = guessit(filename, options=hints)
    if "title" in alt_guess and alt_guess["title"] != guessed_result["title"]:
        if video_type == "episode":
            video.alternative_series.append(alt_guess["title"])
        else:
            video.alternative_titles.append(alt_guess["title"])
        logger.debug("Adding alternative title: %s", alt_guess["title"])

    if dont_use_actual_file and not hash_from:
        return video

    # size and hashes
    if not skip_hashing:
        hash_path = hash_from or path
        video.size = os.path.getsize(hash_path)
        if video.size > 10485760:
            logger.debug('Size is %d', video.size)
            osub_hash = None
            if "opensubtitles" in providers:
                video.hashes['opensubtitles'] = osub_hash = hash_opensubtitles(hash_path)

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


def _search_external_subtitles(path, languages=None, only_one=False, scandir_generic=False, match_strictness="strict"):
    dirpath, filename = os.path.split(path)
    dirpath = dirpath or '.'
    fn_no_ext, fileext = os.path.splitext(filename)
    fn_no_ext_lower = fn_no_ext.lower()
    subtitles = {}
    _scandir = _scandir_generic if scandir_generic else scandir

    for entry in _scandir(dirpath):
        if (not entry.name or entry.name in ('\x0c', '$', ',', '\x7f')) and not scandir_generic:
            logger.debug('Could not determine the name of the file, retrying with scandir_generic')
            return _search_external_subtitles(path, languages, only_one, True)
        if not entry.is_file(follow_symlinks=False):
            continue

        p = entry.name

        # keep only valid subtitle filenames
        if not p.lower().endswith(SUBTITLE_EXTENSIONS):
            continue

        # not p.lower().startswith(fileroot.lower()) or not

        p_root, p_ext = os.path.splitext(p)
        if not INCLUDE_EXOTIC_SUBS and p_ext not in (".srt", ".ass", ".ssa", ".vtt"):
            continue

        # extract potential forced/normal/default tag
        # fixme: duplicate from subtitlehelpers
        split_tag = p_root.rsplit('.', 1)
        adv_tag = None
        if len(split_tag) > 1:
            adv_tag = split_tag[1].lower()
            if adv_tag in ['forced', 'normal', 'default', 'embedded', 'embedded-forced', 'custom']:
                p_root = split_tag[0]

        forced = False
        if adv_tag:
            forced = "forced" in adv_tag

        # remove possible language code for matching
        p_root_bare = ENDSWITH_LANGUAGECODE_RE.sub("", p_root)

        p_root_lower = p_root_bare.lower()

        filename_matches = p_root_lower == fn_no_ext_lower
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
            except (ValueError, LanguageReverseError):
                logger.error('Cannot parse language code %r', language_code)
                language_code = None
        except IndexError:
            language_code = None

        if not language and not language_code and only_one:
            language = Language.rebuild(list(languages)[0], forced=forced)

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
            abspath = unicode(os.path.abspath(
                os.path.join(*[video_path if not os.path.isabs(folder_or_subfolder) else "", folder_or_subfolder,
                               video_filename])))
        except Exception, e:
            logger.error("skipping path %s because of %s", repr(folder_or_subfolder), e)
            continue
        logger.debug("external subs: scanning path %s", abspath)

        if os.path.isdir(os.path.dirname(abspath)):
            try:
                subtitles.update(_search_external_subtitles(abspath, languages=languages,
                                                            only_one=only_one, match_strictness=match_strictness))
            except OSError:
                subtitles.update(_search_external_subtitles(abspath, languages=languages,
                                                            only_one=only_one, match_strictness=match_strictness,
                                                            scandir_generic=True))
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


def download_subtitles(subtitles, pool_class=ProviderPool, **kwargs):
    """Download :attr:`~subliminal.subtitle.Subtitle.content` of `subtitles`.

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
    """List and download the best matching subtitles.

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


def get_subtitle_path(video_path, language=None, extension='.srt', forced_tag=False, tags=None):
    """Get the subtitle path using the `video_path` and `language`.

    :param str video_path: path to the video.
    :param language: language of the subtitle to put in the path.
    :type language: :class:`~babelfish.language.Language`
    :param str extension: extension of the subtitle.
    :return: path of the subtitle.
    :rtype: str

    """
    subtitle_root = os.path.splitext(video_path)[0]
    tags = tags or []
    if forced_tag:
        tags.append("forced")

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
        # check content
        if subtitle.content is None:
            logger.error('Skipping subtitle %r: no content', subtitle)
            continue

        # check language
        if subtitle.language in set(s.language for s in saved_subtitles):
            logger.debug('Skipping subtitle %r: language already saved', subtitle)
            continue

        # create subtitle path
        subtitle_path = get_subtitle_path(file_path, None if single else subtitle.language,
                                          forced_tag=subtitle.language.forced, tags=tags)
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

                with open(subtitle_path, 'w') as f:
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
    """Refine a video using :ref:`refiners`.
    
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
