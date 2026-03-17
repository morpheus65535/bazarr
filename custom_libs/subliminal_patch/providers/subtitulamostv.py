# -*- coding: utf-8 -*-
import logging
import os

from requests import Session
from subzero.language import Language

from guessit import guessit
from subliminal import Episode, __short_version__
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.providers import ParserBeautifulSoup
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider

logger = logging.getLogger(__name__)


class SubtitulamosTVSubtitle(Subtitle):
    provider_name = 'subtitulamostv'
    hash_verifiable = False

    def __init__(self, language, page_link, download_link, release_info):
        super(SubtitulamosTVSubtitle, self).__init__(language, hearing_impaired=False, page_link=page_link)
        self.download_link = download_link
        self.release_info = release_info
        self.matches = set()

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        self.matches = {'series', 'season', 'episode', 'year', 'title'}

        if video.release_group and video.release_group.lower() in self.release_info.lower():
            self.matches.add('release_group')

        self.matches |= guess_matches(video, guessit(self.release_info, {"type": "episode"}))

        return self.matches


class SubtitulamosTVProvider(Provider):
    """Subtitulamostv Provider"""
    languages = {Language.fromietf(lang) for lang in ['en', 'es']}
    video_types = (Episode,)

    server_url = 'https://www.subtitulamos.tv'

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
            if video.series.lower() != serie['show_name'].lower():
                continue

            # season page
            response = self.session.get(self.server_url + "/shows/%d" % serie['show_id'], timeout=10)
            response.raise_for_status()
            soup = ParserBeautifulSoup(response.text, ['lxml', 'html.parser'])
            season_found = False
            for season in soup.select('#season-choices a'):
                if season.text.strip() == str(video.season):
                    season_found = True
                    if "selected" not in season.attrs['class']:
                        # go to the right season page
                        response = self.session.get(self.server_url + season['href'], timeout=10)
                        response.raise_for_status()
                        soup = ParserBeautifulSoup(response.text, ['lxml', 'html.parser'])
                        break
            if not season_found:
                continue

            # episode page
            episode_found = False
            for episode in soup.select('#episode-choices a'):
                if episode.text.strip() == str(video.episode):
                    episode_found = True
                    if "selected" not in episode.attrs['class']:
                        # go to the right episode page
                        response = self.session.get(self.server_url + episode['href'], timeout=10)
                        response.raise_for_status()
                        soup = ParserBeautifulSoup(response.text, ['lxml', 'html.parser'])
                        break
            if not episode_found:
                continue
            episode_url = response.url

            # subtitles
            for lang in soup.select("div.language-container"):
                lang_name = lang.select("div.language-name")[0].text
                if "English" in lang_name:
                    language = "en"
                elif "Español" in lang_name:
                    language = "es"
                else:
                    continue  # not supported yet
                logger.debug('Found subtitles in "%s" language.', language)

                for release in lang.select("div.version-container"):
                    if len(release.select('a[href*="/download"]')) != 1:
                        continue  # incomplete translation, download link is not available

                    release_name = release.select('div.version-container p')[1].text
                    release_url = self.server_url + release.select('a[href*="/download"]')[0]['href']

                    subtitles.append(
                        SubtitulamosTVSubtitle(
                            Language.fromietf(language),
                            episode_url,
                            release_url,
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
