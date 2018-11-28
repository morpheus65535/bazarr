# coding=utf-8
import logging
import rarfile
import os
from subliminal.exceptions import ConfigurationError

from subliminal.providers.legendastv import LegendasTVSubtitle as _LegendasTVSubtitle, \
    LegendasTVProvider as _LegendasTVProvider, Episode, Movie, guess_matches, guessit, sanitize, region, type_map, \
    raise_for_status, json, SHOW_EXPIRATION_TIME, title_re, season_re, datetime, pytz, NO_VALUE, releases_key, \
    SUBTITLE_EXTENSIONS, language_converters
from subzero.language import Language

logger = logging.getLogger(__name__)


class LegendasTVSubtitle(_LegendasTVSubtitle):
    def __init__(self, language, type, title, year, imdb_id, season, archive, name):
        super(LegendasTVSubtitle, self).__init__(language, type, title, year, imdb_id, season, archive, name)
        self.archive.content = None
        self.release_info = archive.name
        self.page_link = archive.link

    def make_picklable(self):
        self.archive.content = None
        return self

    def get_matches(self, video, hearing_impaired=False):
        matches = set()

        # episode
        if isinstance(video, Episode) and self.type == 'episode':
            # series
            if video.series and (sanitize(self.title) in (
                    sanitize(name) for name in [video.series] + video.alternative_series)):
                matches.add('series')

            # year
            if video.original_series and self.year is None or video.year and video.year == self.year:
                matches.add('year')

            # imdb_id
            if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches.add('series_imdb_id')

        # movie
        elif isinstance(video, Movie) and self.type == 'movie':
            # title
            if video.title and (sanitize(self.title) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')

            # year
            if video.year and self.year == video.year:
                matches.add('year')

            # imdb_id
            if video.imdb_id and self.imdb_id == video.imdb_id:
                matches.add('imdb_id')

        # name
        matches |= guess_matches(video, guessit(self.name, {'type': self.type, 'single_value': True}))

        return matches


class LegendasTVProvider(_LegendasTVProvider):
    languages = {Language(*l) for l in language_converters['legendastv'].to_legendastv.keys()}
    subtitle_class = LegendasTVSubtitle

    def __init__(self, username=None, password=None):

        # Provider needs UNRAR installed. If not available raise ConfigurationError
        try:
            rarfile.custom_check([rarfile.UNRAR_TOOL], True)
        except rarfile.RarExecError:
            raise ConfigurationError('UNRAR tool not available')

        if any((username, password)) and not all((username, password)):
            raise ConfigurationError('Username and password must be specified')

        self.username = username
        self.password = password
        self.logged_in = False
        self.session = None

    @staticmethod
    def is_valid_title(title, title_id, sanitized_title, season, year, imdb_id):
        """Check if is a valid title."""
        if title["imdb_id"] and title["imdb_id"] == imdb_id:
            logger.debug(u'Matched title "%s" as IMDB ID %s', sanitized_title, title["imdb_id"])
            return True

        if title["title2"] and sanitize(title['title2']) == sanitized_title:
            logger.debug(u'Matched title "%s" as "%s"', sanitized_title, title["title2"])
            return True

        return _LegendasTVProvider.is_valid_title(title, title_id, sanitized_title, season, year)

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME, should_cache_fn=lambda value: value)
    def search_titles(self, title, season, title_year, imdb_id):
        """Search for titles matching the `title`.

        For episodes, each season has it own title
        :param str title: the title to search for.
        :param int season: season of the title
        :param int title_year: year of the title
        :return: found titles.
        :rtype: dict
        """
        titles = {}
        sanitized_titles = [sanitize(title)]
        ignore_characters = {'\'', '.'}
        if any(c in title for c in ignore_characters):
            sanitized_titles.append(sanitize(title, ignore_characters=ignore_characters))

        for sanitized_title in sanitized_titles:
            # make the query
            if season:
                logger.info('Searching episode title %r for season %r', sanitized_title, season)
            else:
                logger.info('Searching movie title %r', sanitized_title)

            r = self.session.get(self.server_url + 'legenda/sugestao/{}'.format(sanitized_title), timeout=10)
            raise_for_status(r)
            results = json.loads(r.text)

            # loop over results
            for result in results:
                source = result['_source']

                # extract id
                title_id = int(source['id_filme'])

                # extract type
                title = {'type': type_map[source['tipo']], 'title2': None, 'imdb_id': None}

                # extract title, year and country
                name, year, country = title_re.match(source['dsc_nome']).groups()
                title['title'] = name

                if "dsc_nome_br" in source:
                    name2, ommit1, ommit2 = title_re.match(source['dsc_nome_br']).groups()
                    title['title2'] = name2

                # extract imdb_id
                if source['id_imdb'] != '0':
                    if not source['id_imdb'].startswith('tt'):
                        title['imdb_id'] = 'tt' + source['id_imdb'].zfill(7)
                    else:
                        title['imdb_id'] = source['id_imdb']

                # extract season
                if title['type'] == 'episode':
                    if source['temporada'] and source['temporada'].isdigit():
                        title['season'] = int(source['temporada'])
                    else:
                        match = season_re.search(source['dsc_nome_br'])
                        if match:
                            title['season'] = int(match.group('season'))
                        else:
                            logger.debug('No season detected for title %d (%s)', title_id, name)

                # extract year
                if year:
                    title['year'] = int(year)
                elif source['dsc_data_lancamento'] and source['dsc_data_lancamento'].isdigit():
                    # year is based on season air date hence the adjustment
                    title['year'] = int(source['dsc_data_lancamento']) - title.get('season', 1) + 1

                # add title only if is valid
                # Check against title without ignored chars
                if self.is_valid_title(title, title_id, sanitized_titles[0], season, title_year, imdb_id):
                    logger.debug(u'Found title: %s', title)
                    titles[title_id] = title

            logger.debug('Found %d titles', len(titles))

        return titles

    def query(self, language, title, season=None, episode=None, year=None, imdb_id=None):
        # search for titles
        titles = self.search_titles(title, season, year, imdb_id)

        subtitles = []
        # iterate over titles
        for title_id, t in titles.items():

            logger.info('Getting archives for title %d and language %d', title_id, language.legendastv)
            archives = self.get_archives(title_id, language.legendastv, t['type'], season, episode)
            if not archives:
                logger.info('No archives found for title %d and language %d', title_id, language.legendastv)

            # iterate over title's archives
            for a in archives:

                # compute an expiration time based on the archive timestamp
                expiration_time = (datetime.utcnow().replace(tzinfo=pytz.utc) - a.timestamp).total_seconds()

                # attempt to get the releases from the cache
                cache_key = releases_key.format(archive_id=a.id, archive_name=a.name)
                releases = region.get(cache_key, expiration_time=expiration_time)

                # the releases are not in cache or cache is expired
                if releases == NO_VALUE:
                    logger.info('Releases not found in cache')

                    # download archive
                    self.download_archive(a)

                    # extract the releases
                    releases = []
                    for name in a.content.namelist():
                        # discard the legendastv file
                        if name.startswith('Legendas.tv'):
                            continue

                        # discard hidden files
                        if os.path.split(name)[-1].startswith('.'):
                            continue

                        # discard non-subtitle files
                        if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                            continue

                        releases.append(name)

                    # cache the releases
                    region.set(cache_key, releases)

                # iterate over releases
                for r in releases:
                    subtitle = self.subtitle_class(language, t['type'], t['title'], t.get('year'), t.get('imdb_id'),
                                                   t.get('season'), a, r)
                    logger.debug('Found subtitle %r', subtitle)
                    subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        season = episode = None
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
            season = video.season
            episode = video.episode
        else:
            titles = [video.title] + video.alternative_titles

        for title in titles:
            subtitles = [s for l in languages for s in
                         self.query(l, title, season=season, episode=episode, year=video.year, imdb_id=video.imdb_id)]
            if subtitles:
                return subtitles

        return []

    def download_subtitle(self, subtitle):
        super(LegendasTVProvider, self).download_subtitle(subtitle)
        subtitle.archive.content = None

    def get_archives(self, title_id, language_code, title_type, season, episode):
        return super(LegendasTVProvider, self).get_archives.original(self, title_id, language_code, title_type,
                                                                     season, episode)
