# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import io
import rarfile
import zipfile

from babelfish import language_converters
from guessit import guessit
from requests import Session
from subzero.language import Language

from subliminal import Movie, Episode, ProviderError, __short_version__
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import fix_line_ending, SUBTITLE_EXTENSIONS
from subliminal_patch.providers import Provider
from subzero.language import Language

logger = logging.getLogger(__name__)

server_url = 'https://subtitulamos.tv/'


class SubtitulamosTVSubtitle(Subtitle):
    provider_name = 'subtitulamostv'

    def __init__(self, subtitle_id, language, release_group, url, matches):
        super(SubtitulamosTVSubtitle, self).__init__(language, page_link=url)
        self.subtitle_id = subtitle_id
        self.release_group = release_group
        self.download_url = url
        self.matches = matches

    @property
    def id(self):
        return self.subtitle_id

    @property
    def download_link(self):
        return self.download_url

    def get_matches(self, video):
        matches = self.matches

        if isinstance(video, Episode):
            matches |= guess_matches(video, guessit(
                self.release_group, {'type': 'episode'}), partial=True)

        return matches


class SubtitulamosTVProvider(Provider):
    """Subtitulamostv Provider"""
    languages = {Language.fromietf(l) for l in ['en','es-AR','es-ES']}
    video_types = (Episode,)

    # def __init__(self):
    #     if not token:
    #         raise ConfigurationError('Token must be specified')
    #     self.token = token

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        # query the server
        result = None
        matches = set()
        
        q = "%s %dx%02d" % (video.series, video.season, video.episode)
        logger.debug('Searching subtitles "%s"', q)

        res = self.session.get(
            server_url + 'search/query', params={'q':q}, timeout=10)
        res.raise_for_status()
        result = res.json()

        subtitles = []
        for s in [s for s in result if len(s['episodes'])]:
            for e in s['episodes']:
                res = self.session.get(
                    server_url + 'episodes/%d' % e['id'], timeout=10)
                res.raise_for_status()
                html = res.text
                for lang_m in re.finditer(r"<div class=\"subtitle_language\">(.*?)<\/div>.*?(?=<div class=\"subtitle_language\">|<div id=\"subtitle-actions\">)", html, re.S):
                    lang = lang_m.group(1)
                    language = "es"
                    if "Latino" in lang:
                        language = "es-AR"
                    elif "(Espa" in lang:
                        language = "es-ES"
                    elif "English" in lang:
                        language = "en"
                    logger.debug('Found subtitles in "%s" language.', language)

                    for subt_m in re.finditer(r"<div class=\"version_name\">(.*?)</div>.*?<a href=\"/(subtitles/(\d+)/download)\" rel=\"nofollow\">", lang_m.group(0), re.S):
                        logger.debug('Found release "%s".', subt_m.group(1))
                        if video.alternative_series is None:
                            if video.series == s['name']:
                                matches.add('series')
                        elif s['name'] in [video.series]+video.alternative_series:
                            matches.add('series')
                        if video.season == e['season']:
                            matches.add('season')
                        if video.episode == e['number']:
                            matches.add('episode')
                        if video.title == e['name']:
                            matches.add('title')

                        subtitles.append(SubtitulamosTVSubtitle(
                            subt_m.group(3), Language.fromietf(language), subt_m.group(1), server_url + subt_m.group(2), matches))
                        
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        subtitle_content = r.text

        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
        else:
            logger.debug('Could not download subtitle from %s', subtitle.download_link)
