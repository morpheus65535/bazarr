# -*- coding: utf-8 -*-
"""
Subliminal uses `click <http://click.pocoo.org>`_ to provide a powerful :abbr:`CLI (command-line interface)`.

"""
from __future__ import division
from collections import defaultdict
from datetime import timedelta
import glob
import json
import logging
import os
import re

from appdirs import AppDirs
from babelfish import Error as BabelfishError, Language
import click
from dogpile.cache.backends.file import AbstractFileLock
from dogpile.util.readwrite_lock import ReadWriteMutex
from six.moves import configparser

from subliminal import (AsyncProviderPool, Episode, Movie, Video, __version__, check_video, compute_score, get_scores,
                        provider_manager, refine, refiner_manager, region, save_subtitles, scan_video, scan_videos)
from subliminal.core import ARCHIVE_EXTENSIONS, search_external_subtitles

logger = logging.getLogger(__name__)


class MutexLock(AbstractFileLock):
    """:class:`MutexLock` is a thread-based rw lock based on :class:`dogpile.core.ReadWriteMutex`."""
    def __init__(self, filename):
        self.mutex = ReadWriteMutex()

    def acquire_read_lock(self, wait):
        ret = self.mutex.acquire_read_lock(wait)
        return wait or ret

    def acquire_write_lock(self, wait):
        ret = self.mutex.acquire_write_lock(wait)
        return wait or ret

    def release_read_lock(self):
        return self.mutex.release_read_lock()

    def release_write_lock(self):
        return self.mutex.release_write_lock()


class Config(object):
    """A :class:`~configparser.ConfigParser` wrapper to store configuration.

    Interaction with the configuration is done with the properties.

    :param str path: path to the configuration file.

    """
    def __init__(self, path):
        #: Path to the configuration file
        self.path = path

        #: The underlying configuration object
        self.config = configparser.SafeConfigParser()
        self.config.add_section('general')
        self.config.set('general', 'languages', json.dumps(['en']))
        self.config.set('general', 'providers', json.dumps(sorted([p.name for p in provider_manager])))
        self.config.set('general', 'refiners', json.dumps(sorted([r.name for r in refiner_manager])))
        self.config.set('general', 'single', str(0))
        self.config.set('general', 'embedded_subtitles', str(1))
        self.config.set('general', 'age', str(int(timedelta(weeks=2).total_seconds())))
        self.config.set('general', 'hearing_impaired', str(1))
        self.config.set('general', 'min_score', str(0))

    def read(self):
        """Read the configuration from :attr:`path`"""
        self.config.read(self.path)

    def write(self):
        """Write the configuration to :attr:`path`"""
        with open(self.path, 'w') as f:
            self.config.write(f)

    @property
    def languages(self):
        return {Language.fromietf(l) for l in json.loads(self.config.get('general', 'languages'))}

    @languages.setter
    def languages(self, value):
        self.config.set('general', 'languages', json.dumps(sorted([str(l) for l in value])))

    @property
    def providers(self):
        return json.loads(self.config.get('general', 'providers'))

    @providers.setter
    def providers(self, value):
        self.config.set('general', 'providers', json.dumps(sorted([p.lower() for p in value])))

    @property
    def refiners(self):
        return json.loads(self.config.get('general', 'refiners'))

    @refiners.setter
    def refiners(self, value):
        self.config.set('general', 'refiners', json.dumps([r.lower() for r in value]))

    @property
    def single(self):
        return self.config.getboolean('general', 'single')

    @single.setter
    def single(self, value):
        self.config.set('general', 'single', str(int(value)))

    @property
    def embedded_subtitles(self):
        return self.config.getboolean('general', 'embedded_subtitles')

    @embedded_subtitles.setter
    def embedded_subtitles(self, value):
        self.config.set('general', 'embedded_subtitles', str(int(value)))

    @property
    def age(self):
        return timedelta(seconds=self.config.getint('general', 'age'))

    @age.setter
    def age(self, value):
        self.config.set('general', 'age', str(int(value.total_seconds())))

    @property
    def hearing_impaired(self):
        return self.config.getboolean('general', 'hearing_impaired')

    @hearing_impaired.setter
    def hearing_impaired(self, value):
        self.config.set('general', 'hearing_impaired', str(int(value)))

    @property
    def min_score(self):
        return self.config.getfloat('general', 'min_score')

    @min_score.setter
    def min_score(self, value):
        self.config.set('general', 'min_score', str(value))

    @property
    def provider_configs(self):
        rv = {}
        for provider in provider_manager:
            if self.config.has_section(provider.name):
                rv[provider.name] = {k: v for k, v in self.config.items(provider.name)}
        return rv

    @provider_configs.setter
    def provider_configs(self, value):
        # loop over provider configurations
        for provider, config in value.items():
            # create the corresponding section if necessary
            if not self.config.has_section(provider):
                self.config.add_section(provider)

            # add config options
            for k, v in config.items():
                self.config.set(provider, k, v)


class LanguageParamType(click.ParamType):
    """:class:`~click.ParamType` for languages that returns a :class:`~babelfish.language.Language`"""
    name = 'language'

    def convert(self, value, param, ctx):
        try:
            return Language.fromietf(value)
        except BabelfishError:
            self.fail('%s is not a valid language' % value)

LANGUAGE = LanguageParamType()


class AgeParamType(click.ParamType):
    """:class:`~click.ParamType` for age strings that returns a :class:`~datetime.timedelta`

    An age string is in the form `number + identifier` with possible identifiers:

        * ``w`` for weeks
        * ``d`` for days
        * ``h`` for hours

    The form can be specified multiple times but only with that idenfier ordering. For example:

        * ``1w2d4h`` for 1 week, 2 days and 4 hours
        * ``2w`` for 2 weeks
        * ``3w6h`` for 3 weeks and 6 hours

    """
    name = 'age'

    def convert(self, value, param, ctx):
        match = re.match(r'^(?:(?P<weeks>\d+?)w)?(?:(?P<days>\d+?)d)?(?:(?P<hours>\d+?)h)?$', value)
        if not match:
            self.fail('%s is not a valid age' % value)

        return timedelta(**{k: int(v) for k, v in match.groupdict(0).items()})

AGE = AgeParamType()

PROVIDER = click.Choice(sorted(provider_manager.names()))

REFINER = click.Choice(sorted(refiner_manager.names()))

dirs = AppDirs('subliminal')
cache_file = 'subliminal.dbm'
config_file = 'config.ini'


@click.group(context_settings={'max_content_width': 100}, epilog='Suggestions and bug reports are greatly appreciated: '
             'https://github.com/Diaoul/subliminal/')
@click.option('--addic7ed', type=click.STRING, nargs=2, metavar='USERNAME PASSWORD', help='Addic7ed configuration.')
@click.option('--legendastv', type=click.STRING, nargs=2, metavar='USERNAME PASSWORD', help='LegendasTV configuration.')
@click.option('--opensubtitles', type=click.STRING, nargs=2, metavar='USERNAME PASSWORD',
              help='OpenSubtitles configuration.')
@click.option('--cache-dir', type=click.Path(writable=True, file_okay=False), default=dirs.user_cache_dir,
              show_default=True, expose_value=True, help='Path to the cache directory.')
@click.option('--debug', is_flag=True, help='Print useful information for debugging subliminal and for reporting bugs.')
@click.version_option(__version__)
@click.pass_context
def subliminal(ctx, addic7ed, legendastv, opensubtitles, cache_dir, debug):
    """Subtitles, faster than your thoughts."""
    # create cache directory
    try:
        os.makedirs(cache_dir)
    except OSError:
        if not os.path.isdir(cache_dir):
            raise

    # configure cache
    region.configure('dogpile.cache.dbm', expiration_time=timedelta(days=30),
                     arguments={'filename': os.path.join(cache_dir, cache_file), 'lock_factory': MutexLock})

    # configure logging
    if debug:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        logging.getLogger('subliminal').addHandler(handler)
        logging.getLogger('subliminal').setLevel(logging.DEBUG)

    # provider configs
    ctx.obj = {'provider_configs': {}}
    if addic7ed:
        ctx.obj['provider_configs']['addic7ed'] = {'username': addic7ed[0], 'password': addic7ed[1]}
    if legendastv:
        ctx.obj['provider_configs']['legendastv'] = {'username': legendastv[0], 'password': legendastv[1]}
    if opensubtitles:
        ctx.obj['provider_configs']['opensubtitles'] = {'username': opensubtitles[0], 'password': opensubtitles[1]}


@subliminal.command()
@click.option('--clear-subliminal', is_flag=True, help='Clear subliminal\'s cache. Use this ONLY if your cache is '
              'corrupted or if you experience issues.')
@click.pass_context
def cache(ctx, clear_subliminal):
    """Cache management."""
    if clear_subliminal:
        for file in glob.glob(os.path.join(ctx.parent.params['cache_dir'], cache_file) + '*'):
            os.remove(file)
        click.echo('Subliminal\'s cache cleared.')
    else:
        click.echo('Nothing done.')


@subliminal.command()
@click.option('-l', '--language', type=LANGUAGE, required=True, multiple=True, help='Language as IETF code, '
              'e.g. en, pt-BR (can be used multiple times).')
@click.option('-p', '--provider', type=PROVIDER, multiple=True, help='Provider to use (can be used multiple times).')
@click.option('-r', '--refiner', type=REFINER, multiple=True, help='Refiner to use (can be used multiple times).')
@click.option('-a', '--age', type=AGE, help='Filter videos newer than AGE, e.g. 12h, 1w2d.')
@click.option('-d', '--directory', type=click.STRING, metavar='DIR', help='Directory where to save subtitles, '
              'default is next to the video file.')
@click.option('-e', '--encoding', type=click.STRING, metavar='ENC', help='Subtitle file encoding, default is to '
              'preserve original encoding.')
@click.option('-s', '--single', is_flag=True, default=False, help='Save subtitle without language code in the file '
              'name, i.e. use .srt extension. Do not use this unless your media player requires it.')
@click.option('-f', '--force', is_flag=True, default=False, help='Force download even if a subtitle already exist.')
@click.option('-hi', '--hearing-impaired', is_flag=True, default=False, help='Prefer hearing impaired subtitles.')
@click.option('-m', '--min-score', type=click.IntRange(0, 100), default=0, help='Minimum score for a subtitle '
              'to be downloaded (0 to 100).')
@click.option('-w', '--max-workers', type=click.IntRange(1, 50), default=None, help='Maximum number of threads to use.')
@click.option('-z/-Z', '--archives/--no-archives', default=True, show_default=True, help='Scan archives for videos '
              '(supported extensions: %s).' % ', '.join(ARCHIVE_EXTENSIONS))
@click.option('-v', '--verbose', count=True, help='Increase verbosity.')
@click.argument('path', type=click.Path(), required=True, nargs=-1)
@click.pass_obj
def download(obj, provider, refiner, language, age, directory, encoding, single, force, hearing_impaired, min_score,
             max_workers, archives, verbose, path):
    """Download best subtitles.

    PATH can be an directory containing videos, a video file path or a video file name. It can be used multiple times.

    If an existing subtitle is detected (external or embedded) in the correct language, the download is skipped for
    the associated video.

    """
    # process parameters
    language = set(language)

    # scan videos
    videos = []
    ignored_videos = []
    errored_paths = []
    with click.progressbar(path, label='Collecting videos', item_show_func=lambda p: p or '') as bar:
        for p in bar:
            logger.debug('Collecting path %s', p)

            # non-existing
            if not os.path.exists(p):
                try:
                    video = Video.fromname(p)
                except:
                    logger.exception('Unexpected error while collecting non-existing path %s', p)
                    errored_paths.append(p)
                    continue
                if not force:
                    video.subtitle_languages |= set(search_external_subtitles(video.name, directory=directory).values())
                refine(video, episode_refiners=refiner, movie_refiners=refiner, embedded_subtitles=not force)
                videos.append(video)
                continue

            # directories
            if os.path.isdir(p):
                try:
                    scanned_videos = scan_videos(p, age=age, archives=archives)
                except:
                    logger.exception('Unexpected error while collecting directory path %s', p)
                    errored_paths.append(p)
                    continue
                for video in scanned_videos:
                    if not force:
                        video.subtitle_languages |= set(search_external_subtitles(video.name,
                                                                                  directory=directory).values())
                    if check_video(video, languages=language, age=age, undefined=single):
                        refine(video, episode_refiners=refiner, movie_refiners=refiner, embedded_subtitles=not force)
                        videos.append(video)
                    else:
                        ignored_videos.append(video)
                continue

            # other inputs
            try:
                video = scan_video(p)
            except:
                logger.exception('Unexpected error while collecting path %s', p)
                errored_paths.append(p)
                continue
            if not force:
                video.subtitle_languages |= set(search_external_subtitles(video.name, directory=directory).values())
            if check_video(video, languages=language, age=age, undefined=single):
                refine(video, episode_refiners=refiner, movie_refiners=refiner, embedded_subtitles=not force)
                videos.append(video)
            else:
                ignored_videos.append(video)

    # output errored paths
    if verbose > 0:
        for p in errored_paths:
            click.secho('%s errored' % p, fg='red')

    # output ignored videos
    if verbose > 1:
        for video in ignored_videos:
            click.secho('%s ignored - subtitles: %s / age: %d day%s' % (
                os.path.split(video.name)[1],
                ', '.join(str(s) for s in video.subtitle_languages) or 'none',
                video.age.days,
                's' if video.age.days > 1 else ''
            ), fg='yellow')

    # report collected videos
    click.echo('%s video%s collected / %s video%s ignored / %s error%s' % (
        click.style(str(len(videos)), bold=True, fg='green' if videos else None),
        's' if len(videos) > 1 else '',
        click.style(str(len(ignored_videos)), bold=True, fg='yellow' if ignored_videos else None),
        's' if len(ignored_videos) > 1 else '',
        click.style(str(len(errored_paths)), bold=True, fg='red' if errored_paths else None),
        's' if len(errored_paths) > 1 else '',
    ))

    # exit if no video collected
    if not videos:
        return

    # download best subtitles
    downloaded_subtitles = defaultdict(list)
    with AsyncProviderPool(max_workers=max_workers, providers=provider, provider_configs=obj['provider_configs']) as p:
        with click.progressbar(videos, label='Downloading subtitles',
                               item_show_func=lambda v: os.path.split(v.name)[1] if v is not None else '') as bar:
            for v in bar:
                scores = get_scores(v)
                subtitles = p.download_best_subtitles(p.list_subtitles(v, language - v.subtitle_languages),
                                                      v, language, min_score=scores['hash'] * min_score / 100,
                                                      hearing_impaired=hearing_impaired, only_one=single)
                downloaded_subtitles[v] = subtitles

        if p.discarded_providers:
            click.secho('Some providers have been discarded due to unexpected errors: %s' %
                        ', '.join(p.discarded_providers), fg='yellow')

    # save subtitles
    total_subtitles = 0
    for v, subtitles in downloaded_subtitles.items():
        saved_subtitles = save_subtitles(v, subtitles, single=single, directory=directory, encoding=encoding)
        total_subtitles += len(saved_subtitles)

        if verbose > 0:
            click.echo('%s subtitle%s downloaded for %s' % (click.style(str(len(saved_subtitles)), bold=True),
                                                            's' if len(saved_subtitles) > 1 else '',
                                                            os.path.split(v.name)[1]))

        if verbose > 1:
            for s in saved_subtitles:
                matches = s.get_matches(v)
                score = compute_score(s, v)

                # score color
                score_color = None
                scores = get_scores(v)
                if isinstance(v, Movie):
                    if score < scores['title']:
                        score_color = 'red'
                    elif score < scores['title'] + scores['year'] + scores['release_group']:
                        score_color = 'yellow'
                    else:
                        score_color = 'green'
                elif isinstance(v, Episode):
                    if score < scores['series'] + scores['season'] + scores['episode']:
                        score_color = 'red'
                    elif score < scores['series'] + scores['season'] + scores['episode'] + scores['release_group']:
                        score_color = 'yellow'
                    else:
                        score_color = 'green'

                # scale score from 0 to 100 taking out preferences
                scaled_score = score
                if s.hearing_impaired == hearing_impaired:
                    scaled_score -= scores['hearing_impaired']
                scaled_score *= 100 / scores['hash']

                # echo some nice colored output
                click.echo('  - [{score}] {language} subtitle from {provider_name} (match on {matches})'.format(
                    score=click.style('{:5.1f}'.format(scaled_score), fg=score_color, bold=score >= scores['hash']),
                    language=s.language.name if s.language.country is None else '%s (%s)' % (s.language.name,
                                                                                             s.language.country.name),
                    provider_name=s.provider_name,
                    matches=', '.join(sorted(matches, key=scores.get, reverse=True))
                ))

    if verbose == 0:
        click.echo('Downloaded %s subtitle%s' % (click.style(str(total_subtitles), bold=True),
                                                 's' if total_subtitles > 1 else ''))
