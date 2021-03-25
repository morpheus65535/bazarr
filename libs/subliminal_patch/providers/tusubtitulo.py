# -*- coding: utf-8 -*-
import logging

import random
import re

from urllib import parse

from bs4 import BeautifulSoup as bso
from requests import Session
from subzero.language import Language
from guessit import guessit

from subliminal import Episode
from subliminal.exceptions import ServiceUnavailable
from subliminal_patch.exceptions import APIThrottled
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending, guess_matches

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)


BASE_URL = "https://www.tusubtitulo.com"
CSS1 = "span.iconos-subtitulos"
CSS2 = "ul > li.rng.download.green > a.fas.fa-bullhorn.notifi_icon"


class TuSubtituloSubtitle(Subtitle):
    provider_name = "tusubtitulo"
    hash_verifiable = False

    def __init__(self, language, sub_dict, matches):
        super(TuSubtituloSubtitle, self).__init__(
            language, hearing_impaired=False, page_link=sub_dict["download_url"]
        )
        self.language = language
        self.sub_dict = sub_dict
        self.release_info = sub_dict["metadata"]
        self.found_matches = matches

    @property
    def id(self):
        return self.sub_dict["download_url"]

    def get_matches(self, video):
        self.found_matches |= guess_matches(
            video,
            guessit(
                self.release_info,
                {"type": "episode"},
            ),
        )
        return self.found_matches


class TuSubtituloProvider(Provider):
    """TuSubtitulo.com Provider"""

    languages = {Language.fromietf(lang) for lang in ["en", "es"]}
    logger.debug(languages)
    video_types = (Episode,)

    def initialize(self):
        self.session = Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
            "referer": BASE_URL,
        }

    def terminate(self):
        self.session.close()

    def index_titles(self):
        r = self.session.get(f"{BASE_URL}/series.php?/")
        r.raise_for_status()
        soup = bso(r.content, "html.parser")

        for a in soup.find_all("a"):
            href_url = a.get("href")
            if "show" in href_url:
                yield {"title": a.text, "url": href_url}

    def title_available(self, item):
        try:
            title = item[2].find_all("a")[0]
            episode_number = re.search(r".*\d+x(0+)?(\d+) - .*?", title.text).group(2)
            episode_id = title.get("href").split("/")[4]
            return {"episode_number": episode_number, "episode_id": episode_id}
        except IndexError:
            return

    def source_separator(self, item):
        try:
            text = item[3].text.replace("\n", "")
            if "Vers" in text:
                source = text.replace("Versión ", "")
                if not source:
                    return "Unknown"
                return source
        except IndexError:
            return

    def get_episode_dicts(self, episodes, season_subs, season_number):
        for i in episodes:
            for t in season_subs:
                if i["episode_id"] == t["episode_id"]:
                    yield {
                        "episode": i["episode_number"],
                        "season": season_number,
                        "metadata": t["metadata"],
                        "download_url": t["download_url"],
                        "language": t["language"],
                    }

    def scrape_episode_info(self, source_var, tables, tr):
        inc = 1
        while True:
            try:
                content = tables[tr + inc].find_all("td")

                language = content[4].text
                if "eng" in language.lower():
                    language = "en"
                elif "esp" in language.lower():
                    language = "es"
                else:
                    language = None

                completed = "%" not in content[5].text
                download_url = (
                    content[6].find_all("a")[1].get("href").split("?sub=")[-1]
                )
                episode_id = download_url.split("/")[4]

                if language and completed:
                    yield {
                        "episode_id": episode_id,
                        "metadata": source_var,
                        "download_url": download_url,
                        "language": language,
                    }
                inc += 1
            except IndexError:
                break

    def get_episodes(self, show_id, season):
        r = self.session.get(f"{BASE_URL}/show/{show_id}/{season}")
        r.raise_for_status()
        sopa = bso(r.content, "lxml")
        tables = sopa.find_all("tr")
        seasons = [i.text for i in tables[1].find_all("a")]

        if not any(season == season_ for season_ in seasons):
            return

        season_subs = []
        episodes = []

        for tr in range(len(tables)):
            data = tables[tr].find_all("td")

            title = self.title_available(data)
            if title:
                episodes.append(title)

            source_var = self.source_separator(data)
            if not source_var:
                continue

            season_subs += list(self.scrape_episode_info(source_var, tables, tr))

        return list(self.get_episode_dicts(episodes, season_subs, season))

    def search(self, title, season, episode):
        titles = list(self.index_titles())
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
                if i["episode"] == episode:
                    episode_list.append(i)
            if episode_list:
                return episode_list
            else:
                logger.debug("No results")

        logger.debug("No results")

    def scrape_download_url(self, episode_dict):
        logger.debug("Scrapping download URL")
        r = self.session.get(episode_dict["download_url"])
        r.raise_for_status()

        discriminator = f".{episode_dict['season']}.{episode_dict['episode']}."
        soup = bso(r.content, "lxml")

        for url, selected in zip(soup.select(CSS1), soup.select(CSS2)):
            meta = ".".join(
                selected.get("href").split(discriminator)[-1].split(".")[:-1]
            )
            if meta in episode_dict["download_url"]:

                id_url = url.find_all("a")[0].get("href")
                sub_id = parse.parse_qs(parse.urlparse(id_url).query)["id"][0]
                lang_id = parse.parse_qs(parse.urlparse(id_url).query)["lang"][0]
                version_ = parse.parse_qs(parse.urlparse(id_url).query)["fversion"][0]

                return f"{BASE_URL}/updated/{lang_id}/{sub_id}/{version_}"

    def query(self, languages, video):
        query = f"{video.series} {video.season} {video.episode}"
        logger.debug(f"Searching subtitles: {query}")
        results = self.search(video.series, str(video.season), str(video.episode))

        if results:
            subtitles = []
            for sub in results:
                matches = set()
                # self.search only returns results for the specific episode
                matches_ = ("title", "series", "season", "episode", "year")
                [matches.add(match) for match in matches_]
                subtitles.append(
                    TuSubtituloSubtitle(
                        Language.fromietf(sub["language"]),
                        sub,
                        matches,
                    )
                )
            return subtitles

        logger.debug("No subtitles found")
        return []

    def list_subtitles(self, video, languages):
        return self.query(languages, video)

    def _check_response(self, response):
        if response.status_code != 200:
            raise ServiceUnavailable(f"Bad status code: {response.status_code}")

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle %r", subtitle)
        download_url_ = self.scrape_download_url(subtitle.sub_dict)

        if not download_url_:
            raise APIThrottled("Can't scrape download url")

        response = self.session.get(download_url_, timeout=10, allow_redirects=True)
        response.raise_for_status()
        self._check_response(response)
        subtitle.content = fix_line_ending(response.content)
