# coding=utf-8
import logging
import os
import io
import time

from zipfile import ZipFile
from guessit import guessit
from requests import Session
from subliminal import Episode, Movie
from subliminal.score import get_equivalent_release_groups
from subliminal.utils import sanitize_release_group, sanitize
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subzero.language import Language

logger = logging.getLogger(__name__)


class ArgenteamSubtitle(Subtitle):
    provider_name = 'argenteam'
    hearing_impaired_verifiable = False
    _release_info = None

    def __init__(self, language, page_link, download_link, movie_kind, title, season, episode, year, release, version, source,
                 video_codec, tvdb_id, imdb_id, asked_for_episode=None, asked_for_release_group=None, *args, **kwargs):
        super(ArgenteamSubtitle, self).__init__(language, page_link=page_link, *args, **kwargs)
        self.page_link = page_link
        self.download_link = download_link
        self.movie_kind = movie_kind
        self.title = title
        self.year = year
        self.season = season
        self.episode = episode
        self.release = release
        self.version = version
        self.asked_for_release_group = asked_for_release_group
        self.asked_for_episode = asked_for_episode
        self.matches = None
        self.format = source
        self.video_codec = video_codec
        self.tvdb_id = tvdb_id
        self.imdb_id = "tt" + imdb_id if imdb_id else None
        self.releases = self.release_info

    @property
    def id(self):
        return self.download_link

    @property
    def release_info(self):
        if self._release_info:
            return self._release_info

        combine = []
        for attr in ("format", "version", "video_codec"):
            value = getattr(self, attr)
            if value:
                combine.append(value)

        self._release_info = u".".join(combine) + (u"-"+self.release if self.release else "")
        return self._release_info

    def __repr__(self):
        ep_addon = (" S%02dE%02d" % (self.season, self.episode)) if self.episode else ""
        return '<%s %r [%s]>' % (
            self.__class__.__name__, u"%s%s%s." % (self.title, " (%s)" % self.year if self.year else "", ep_addon) +
            self.release_info, self.language)

    def get_matches(self, video):
        matches = set()
        # series
        if isinstance(video, Episode) and self.movie_kind == 'episode':
            if video.series and (sanitize(self.title) in (
                     sanitize(name) for name in [video.series] + video.alternative_series)):
                matches.add('series')
            # season
            if video.season and self.season == video.season:
                matches.add('season')
            # episode
            if video.episode and self.episode == video.episode:
                matches.add('episode')

            # tvdb_id
            if video.tvdb_id and str(self.tvdb_id) == str(video.tvdb_id):
                matches.add('tvdb_id')

        elif isinstance(video, Movie) and self.movie_kind == 'movie':
            # title
            if video.title and (sanitize(self.title) in (
                     sanitize(name) for name in [video.title] + video.alternative_titles)):
                matches.add('title')

            # imdb_id
            if video.imdb_id and self.imdb_id and str(self.imdb_id) == str(video.imdb_id):
                matches.add('imdb_id')

            # year
            if video.year and self.year == video.year:
                matches.add('year')
        else:
            logger.info('%r is not a valid movie_kind', self.movie_kind)
            return matches

        # release_group
        if video.release_group and self.release:
            rg = sanitize_release_group(video.release_group)
            if any(r in sanitize_release_group(self.release) for r in get_equivalent_release_groups(rg)):
                matches.add('release_group')

                # blatantly assume we've got a matching format if the release group matches
                # fixme: smart?
                #matches.add('format')

        # resolution
        if video.resolution and self.version and str(video.resolution) in self.version.lower():
            matches.add('resolution')
        # format
        if video.format and self.format:
            formats = [video.format]
            if video.format == "WEB-DL":
                formats.append("WEB")

            for fmt in formats:
                if fmt.lower() in self.format.lower():
                    matches.add('format')
                    break

        matches |= guess_matches(video, guessit(self.release_info), partial=True)
        self.matches = matches
        return matches


class ArgenteamProvider(Provider, ProviderSubtitleArchiveMixin):
    provider_name = 'argenteam'
    languages = {Language.fromalpha2(l) for l in ['es']}
    video_types = (Episode, Movie)
    BASE_URL = "https://argenteam.net/"
    API_URL = BASE_URL + "api/v1/"
    subtitle_class = ArgenteamSubtitle
    hearing_impaired_verifiable = False
    language_list = list(languages)

    multi_result_throttle = 2  # seconds

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers = {'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}

    def terminate(self):
        self.session.close()

    def search_ids(self, title, year=None, imdb_id=None, season=None, episode=None, titles=None):
        """Search movie or episode id from the `title`, `season` and `episode`.

        :param imdb_id: imdb id of the given movie
        :param titles: all titles of the given series or movie
        :param year: release year of the given movie
        :param str title: series of the episode or movie name
        :param int season: season of the episode.
        :param int episode: episode number.
        :return: list of ids
        :rtype: list

        """
        # make the search
        query = title
        titles = titles or []

        is_episode = False
        if season and episode:
            is_episode = True
            query = '%s S%#02dE%#02d' % (title, season, episode)

        logger.info(u'Searching %s ID for %r', "episode" if is_episode else "movie", query)
        r = self.session.get(self.API_URL + 'search', params={'q': query}, timeout=10)
        r.raise_for_status()
        results = r.json()
        match_ids = []
        if results['total'] >= 1:
            for result in results["results"]:
                if (result['type'] == "episode" and not is_episode) or (result['type'] == "movie" and is_episode):
                    continue

                # shortcut in case of matching imdb id
                if not is_episode and imdb_id and "imdb" in result and "tt%s" % result["imdb"] == str(imdb_id):
                    logger.debug("Movie matched by IMDB ID %s, taking shortcut", imdb_id)
                    match_ids = [result['id']]
                    break

                # advanced title check in case of multiple movie results
                if results['total'] > 1:
                    if not is_episode and year:
                        if result["title"] and not (sanitize(result["title"]) in (u"%s %s" % (sanitize(name), year)
                                                                                  for name in titles)):
                            continue

                match_ids.append(result['id'])
        else:
            logger.error(u'No episode ID found for %r', query)

        if match_ids:
            logger.debug(u"Found matching IDs: %s", ", ".join(str(id) for id in match_ids))

        return match_ids

    def query(self, title, video, titles=None):
        is_episode = isinstance(video, Episode)
        season = episode = None
        url = self.API_URL + 'movie'
        if is_episode:
            season = video.season
            episode = video.episode
            url = self.API_URL + 'episode'
            argenteam_ids = self.search_ids(title, season=season, episode=episode, titles=titles)

        else:
            argenteam_ids = self.search_ids(title, year=video.year, imdb_id=video.imdb_id, titles=titles)

        if not argenteam_ids:
            return []

        language = self.language_list[0]
        subtitles = []
        has_multiple_ids = len(argenteam_ids) > 1
        for aid in argenteam_ids:
            response = self.session.get(url, params={'id': aid}, timeout=10)

            response.raise_for_status()
            content = response.json()

            imdb_id = year = None
            returned_title = title
            if not is_episode and "info" in content:
                imdb_id = content["info"].get("imdb")
                year = content["info"].get("year")
                returned_title = content["info"].get("title", title)

            for r in content['releases']:
                for s in r['subtitles']:
                    movie_kind = "episode" if is_episode else "movie"
                    page_link = self.BASE_URL + movie_kind + "/" + str(aid)
                    # use https and new domain
                    download_link = s['uri'].replace('http://www.argenteam.net/', self.BASE_URL)
                    sub = ArgenteamSubtitle(language, page_link, download_link, movie_kind, returned_title,
                                            season, episode, year, r.get('team'), r.get('tags'),
                                            r.get('source'), r.get('codec'), content.get("tvdb"), imdb_id,
                                            asked_for_release_group=video.release_group,
                                            asked_for_episode=episode)
                    subtitles.append(sub)

            if has_multiple_ids:
                time.sleep(self.multi_result_throttle)

        return subtitles

    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
        else:
            titles = [video.title] + video.alternative_titles

        for title in titles:
            subs = self.query(title, video, titles=titles)
            if subs:
                return subs

            time.sleep(self.multi_result_throttle)

        return []

    def download_subtitle(self, subtitle):
        # download as a zip
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        # open the zip
        with ZipFile(io.BytesIO(r.content)) as zf:
            subtitle.content = self.get_subtitle_from_archive(subtitle, zf)
