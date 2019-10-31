# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import io

from babelfish import language_converters
from guessit import guessit
from requests import Session
from subzero.language import Language

from subliminal import Movie, Episode, ProviderError, __short_version__
from subliminal.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.subtitle import fix_line_ending, SUBTITLE_EXTENSIONS
from subliminal_patch.providers import Provider

logger = logging.getLogger(__name__)

server_url = 'https://subtitulamos.tv/'


class SubtitulamosTVSubtitle(Subtitle):
    provider_name = 'subtitulamostv'
    hash_verifiable = False

    def __init__(self, language, page_link, download_link, description, title, matches, release_info):
        super(SubtitulamosTVSubtitle, self).__init__(language, hearing_impaired=False,
                                              page_link=page_link)
        self.download_link = download_link
        self.description = description.lower()
        self.title = title
        self.release_info = release_info
        self.found_matches = matches

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = self.found_matches

        # release_group
        if video.release_group and video.release_group.lower() in self.description:
            matches.add('release_group')

        # resolution
        if video.resolution and video.resolution.lower() in self.description:
            matches.add('resolution')

        # format
        if video.format:
            formats = [video.format.lower()]
            if formats[0] == "web-dl":
                formats.append("webdl")
                formats.append("webrip")
                formats.append("web ")
            for frmt in formats:
                if frmt.lower() in self.description:
                    matches.add('format')
                    break

        # video_codec
        if video.video_codec:
            video_codecs = [video.video_codec.lower()]
            if video_codecs[0] == "h264":
                formats.append("x264")
            elif video_codecs[0] == "h265":
                formats.append("x265")
            for vc in formats:
                if vc.lower() in self.description:
                    matches.add('video_codec')
                    break

        return matches


class SubtitulamosTVProvider(Provider):
    """Subtitulamostv Provider"""
    languages = {Language.fromietf(l) for l in ['en','es']}
    video_types = (Episode,)

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        # query the server
        result = None
        year = (" (%d)" % video.year) if video.year else ""
        q = "%s%s %dx%02d" % (video.series, year, video.season, video.episode)
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
                    if "English" in lang:
                        language = "en"
                    logger.debug('Found subtitles in "%s" language.', language)

                    for subt_m in re.finditer(r"<div class=\"version_name\">(.*?)</div>.*?<a href=\"/(subtitles/\d+/download)\" rel=\"nofollow\">(?:.*?<div class=\"version_comments ?\">.*?</i>(.*?)</p>)?", lang_m.group(0), re.S):
                        matches = set()
                        if video.alternative_series is None:
                            if video.series.lower() == s['name'].lower():
                                matches.add('series')
                        elif s['name'].lower() in [video.series.lower()]+map(lambda name: name.lower(), video.alternative_series):
                            matches.add('series')
                        if video.season == e['season']:
                            matches.add('season')
                        if video.episode == e['number']:
                            matches.add('episode')
                        if video.title == e['name']:
                            matches.add('title')
                        #if video.year is None or ("(%d)" % video.year) in s['name']:
                        matches.add('year')
                        subtitles.append(
                            SubtitulamosTVSubtitle(
                                Language.fromietf(language), 
                                server_url + 'episodes/%d' % e['id'], 
                                server_url + subt_m.group(2),
                                subt_m.group(1)+(subt_m.group(3) if not subt_m.group(3) is None else ""), 
                                e['name'], 
                                matches,
                                '%s %dx%d,%s,%s' % (s['name'], e['season'], e['number'], subt_m.group(1), lang_m.group(1)), 
                            )
                        )
                        
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def download_subtitle(self, subtitle):
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(subtitle.download_link, timeout=10)
        r.raise_for_status()

        r.encoding = "ISO-8859-1"
        subtitle_content = r.text

        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
        else:
            logger.debug('Could not download subtitle from %s', subtitle.download_link)
