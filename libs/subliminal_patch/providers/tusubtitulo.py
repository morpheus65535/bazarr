# -*- coding: utf-8 -*-
import logging
from urllib import parse
import re
from bs4 import BeautifulSoup as bso

from requests import Session
from subzero.language import Language

from subliminal import Episode
from subliminal.exceptions import ServiceUnavailable
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal_patch.providers import Provider

logger = logging.getLogger(__name__)


BASE = "https://www.tusubtitulo.com/series.php?/"


class TuSubtituloSubtitle(Subtitle):
    provider_name = "tusubtitulo"

    def __init__(self, language, filename, download_link, page_link, matches):
        super(TuSubtituloSubtitle, self).__init__(
            language, hearing_impaired=False, page_link=page_link
        )
        self.download_link = download_link
        self.page_link = page_link
        self.language = language
        self.release_info = filename
        self.filename = filename
        self.found_matches = matches

    @property
    def id(self):
        return self.download_link

    def get_matches(self, video):
        if video.resolution and video.resolution.lower() in self.release_info.lower():
            self.found_matches.add("resolution")

        if video.source and video.source.lower() in self.release_info.lower():
            self.found_matches.add("source")

        if video.video_codec:
            if video.video_codec == "H.264" and "x264" in self.release_info.lower():
                self.found_matches.add("video_codec")
            elif video.video_codec == "H.265" and "x265" in self.release_info.lower():
                self.found_matches.add("video_codec")
            elif video.video_codec.lower() in self.release_info.lower():
                self.found_matches.add("video_codec")

        if video.audio_codec:
            if video.audio_codec.lower().replace(" ", ".") in self.release_info.lower():
                self.found_matches.add("audio_codec")
        return self.found_matches


class TuSubtituloProvider(Provider):
    """TuSubtitulo.com Provider"""

    BASE = "https://www.tusubtitulo.com/series.php?/"
    languages = {Language.fromalpha2(l) for l in ["es"]}
    language_list = list(languages)
    logger.debug(languages)
    video_types = (Episode,)

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
            "referer": "https://www.tusubtitulo.com",
        }

    def terminate(self):
        self.session.close()

    def index_titles(self):
        r = self.session.get(BASE)
        r.raise_for_status()
        soup = bso(r.content, "html.parser")
        titles = []
        for a in soup.find_all("a"):
            href_url = a.get("href")
            if "show" in href_url:
                titles.append({"title": a.text, "url": href_url})
        return titles

    def is_season_available(self, seasons, season):
        for i in seasons:
            if i == season:
                return True

    def title_available(self, item):
        try:
            title_content = item[2].find_all("a")[0]
            episode_number = re.search(
                r".*\d+x(0+)?(\d+) - .*?", title_content.text
            ).group(2)
            episode_id = title_content.get("href").split("/")[4]
            return {
                "episode_number": episode_number,
                "episode_id": episode_id,
                "episode_url": title_content.get("href"),
            }
        except IndexError:
            return

    def source_separator(self, item):
        try:
            text = item[3].text.replace("\n", "")
            if "Vers" in text:
                source = text.replace("Versión ", "")
                if not source:
                    source = "Unknown"
                return source
        except IndexError:
            return

    def get_episodes(self, show_id, season):
        logger.debug("https://www.tusubtitulo.com/show/{}/{}".format(show_id, season))
        r2 = self.session.get(
            "https://www.tusubtitulo.com/show/{}/{}".format(show_id, season),
        )
        r2.raise_for_status()
        sopa = bso(r2.content, "lxml")
        tables = sopa.find_all("tr")
        seasons = [i.text for i in tables[1].find_all("a")]
        if not self.is_season_available(seasons, season):
            logger.debug("Season not found")
            return
        season_subs = []
        episodes = []

        for tr in range(len(tables)):
            data = tables[tr].find_all("td")
            title = self.title_available(data)
            if title:
                episodes.append(title)
            source_var = self.source_separator(data)
            if source_var:
                inc = 1
                while True:
                    try:
                        content = tables[tr + inc].find_all("td")
                        language = content[4].text
                        completed = content[5]
                        url = content[6].find_all("a")[0].get("href")
                        sub_id = parse.parse_qs(parse.urlparse(url).query)["id"][0]
                        lang_id = parse.parse_qs(parse.urlparse(url).query)["lang"][0]
                        version_ = parse.parse_qs(parse.urlparse(url).query)["version"][
                            0
                        ]
                        download_url = (
                            "https://www.tusubtitulo.com/updated/{}/{}/{}".format(
                                lang_id, sub_id, version_
                            )
                        )
                        if "esp" in language.lower():
                            season_subs.append(
                                {
                                    "episode_id": sub_id,
                                    "metadata": source_var,
                                    "download_url": download_url,
                                }
                            )
                        inc += 1
                    except IndexError:
                        break

        final_list = []
        for i in episodes:
            for t in season_subs:
                if i["episode_id"] == t["episode_id"]:
                    final_list.append(
                        {
                            "episode_number": i["episode_number"],
                            "episode_url": i["episode_url"],
                            "metadata": t["metadata"],
                            "download_url": t["download_url"],
                        }
                    )
        return final_list

    def search(self, title, season, episode):
        titles = self.index_titles()
        found_tv_show = None
        for i in titles:
            if title.lower() == i["title"].lower():
                found_tv_show = i
                break
        if not found_tv_show:
            logger.debug("Show not found")
            return
        tv_show_id = found_tv_show["url"].split("/")[2].replace(" ", "")
        results = self.get_episodes(tv_show_id, season)
        episode_list = []
        if results:
            for i in results:
                if i["episode_number"] == episode:
                    episode_list.append(i)
            if episode_list:
                return episode_list
        logger.debug("Episode not found")

    def query(self, languages, video):
        language = self.language_list[0]
        query = "{} {} {}".format(video.series, video.season, video.episode)
        logger.debug("Searching subtitles: {}".format(query))
        results = self.search(video.series, str(video.season), str(video.episode))

        if results:
            subtitles = []
            for i in results:
                matches = set()
                # self.search only returns results for the specific episode
                matches.add("title")
                matches.add("series")
                matches.add("season")
                matches.add("episode")
                matches.add("year")
                subtitles.append(
                    TuSubtituloSubtitle(
                        language,
                        i["metadata"],
                        i["download_url"],
                        i["episode_url"],
                        matches,
                    )
                )
            return subtitles
        else:
            logger.debug("No subtitles found")
            return []

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def _check_response(self, response):
        if response.status_code != 200:
            raise ServiceUnavailable("Bad status code: " + str(response.status_code))

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle %r", subtitle)
        response = self.session.get(
            subtitle.download_link, headers={"Referer": subtitle.page_link}, timeout=10
        )
        response.raise_for_status()
        self._check_response(response)
        subtitle.content = fix_line_ending(response.content)
