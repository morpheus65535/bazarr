# -*- coding: utf-8 -*-
import logging
import os

from requests import Session
from subzero.language import Language

from subliminal import Movie, Episode, ProviderError, __short_version__
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import fix_line_ending, SUBTITLE_EXTENSIONS
from subliminal_patch.providers import Provider

logger = logging.getLogger(__name__)


class SubtitulamosTVSubtitle(Subtitle):
    provider_name = 'subtitulamostv'
    hash_verifiable = False

    def __init__(self, language, page_link, download_link, title, release_info):
        super(SubtitulamosTVSubtitle, self).__init__(language, hearing_impaired=False, page_link=page_link)
        self.download_link = download_link
        self.title = title
        self.release_info = release_info

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        matches = {'series', 'season', 'episode', 'year'}

        title_lower = self.title.lower()
        release_info_lower = self.release_info.lower()

        if video.title and video.title.lower() in title_lower:
            matches.add('title')

        if video.release_group and video.release_group.lower() in release_info_lower:
            matches.add('release_group')

        if video.resolution and video.resolution.lower() in release_info_lower:
            matches.add('resolution')

        if video.source:
            formats = [video.source.lower()]
            if formats[0] == "web":
                formats.append("webdl")
                formats.append("web-dl")
                formats.append("webrip")
            for frmt in formats:
                if frmt in release_info_lower:
                    matches.add('source')
                    break

        if video.video_codec:
            video_codecs = [video.video_codec.lower()]
            if video_codecs[0] == "h.264":
                video_codecs.append("h264")
                video_codecs.append("x264")
            elif video_codecs[0] == "h.265":
                video_codecs.append("h265")
                video_codecs.append("x265")
            for vc in video_codecs:
                if vc in release_info_lower:
                    matches.add('video_codec')
                    break

        return matches


class SubtitulamosTVProvider(Provider):
    """Subtitulamostv Provider"""
    languages = {Language.fromietf(lang) for lang in ['en', 'es']}
    video_types = (Episode,)

    server_url = 'https://subtitulamos.tv'

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            'User-Agent': os.environ.get("SZ_USER_AGENT", "Sub-Zero/2")}

    def terminate(self):
        self.session.close()

    def query(self, languages, video):
        subtitle_name = "%s %dx%02d" % (video.series, video.season, video.episode)
        logger.debug('Searching subtitles "%s"' % subtitle_name)

        response = self.session.get(self.server_url + '/search/query', params={'q': video.series}, timeout=10)
        response.raise_for_status()
        result = response.json()

        subtitles = []
        for serie in result:
            # skip non-matching series
            if video.series.lower() != serie['name'].lower():
                continue

            response = self.session.get(self.server_url + "/shows/%d/season/%d" % (serie['id'], video.season),
                                        timeout=10)
            response.raise_for_status()
            soup = ParserBeautifulSoup(response.text, ['lxml', 'html.parser'])

            for episode in soup.select('div.episode'):
                episode_soup = episode.find('a')
                episode_name = episode_soup.text
                episode_url = episode_soup['href']

                # skip non-matching episodes
                if subtitle_name.lower() not in episode_name.lower():
                    continue

                for lang in episode.select("div.subtitle-language"):
                    if "English" in lang.text:
                        language = "en"
                    elif "Español" in lang.text:
                        language = "es"
                    else:
                        continue  # not supported yet
                    logger.debug('Found subtitles in "%s" language.', language)

                    for release in lang.find_next_sibling("div").select("div.sub"):
                        release_name = release.select('div.version-name')[0].text
                        release_url = release.select('a[href*="/download"]')[0]['href']

                        subtitles.append(
                            SubtitulamosTVSubtitle(
                                Language.fromietf(language),
                                self.server_url + episode_url,
                                self.server_url + release_url,
                                episode_name,
                                release_name
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
        subtitle_content = r.content

        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
        else:
            logger.debug('Could not download subtitle from %s', subtitle.download_link)
