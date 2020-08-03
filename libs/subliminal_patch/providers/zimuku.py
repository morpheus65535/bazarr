# -*- coding: utf-8 -*-
from __future__ import absolute_import
import io
import logging
import os
import zipfile
import re
import copy

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

import rarfile
from subzero.language import Language
from guessit import guessit
from requests import Session
from six import text_type

from subliminal import __short_version__
from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.subtitle import (
    SUBTITLE_EXTENSIONS,
    Subtitle,
    fix_line_ending,
    guess_matches,
)
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)


class ZimukuSubtitle(Subtitle):
    """Zimuku Subtitle."""

    provider_name = "zimuku"

    def __init__(self, language, page_link, version, session, year):
        super(ZimukuSubtitle, self).__init__(language, page_link=page_link)
        self.version = version
        self.release_info = version
        self.hearing_impaired = False
        self.encoding = "utf-8"
        self.session = session
        self.year = year

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        matches = set()

        if video.year == self.year:
            matches.add('year')

        # episode
        if isinstance(video, Episode):
            info = guessit(self.version, {"type": "episode"})
            # other properties
            matches |= guess_matches(video, info, partial=True)
        # movie
        elif isinstance(video, Movie):
            # other properties
            matches |= guess_matches(
                video, guessit(self.version, {"type": "movie"}), partial=True
            )

        return matches


class ZimukuProvider(Provider):
    """Zimuku Provider."""

    languages = {Language(l) for l in ["zho", "eng"]}

    server_url = "http://www.zimuku.la"
    search_url = "/search?q={}"
    download_url = "http://www.zimuku.la/"

    UserAgent = "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)"

    subtitle_class = ZimukuSubtitle

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()
        self.session.headers["User-Agent"] = "Subliminal/{}".format(__short_version__)

    def terminate(self):
        self.session.close()

    def _parse_episode_page(self, link, year):
        r = self.session.get(link)
        bs_obj = ParserBeautifulSoup(
            r.content.decode("utf-8", "ignore"), ["html.parser"]
        )
        subs_body = bs_obj.find("div", class_="subs box clearfix").find("tbody")
        subs = []
        for sub in subs_body.find_all("tr"):
            a = sub.find("a")
            name = _extract_name(a.text)
            name = os.path.splitext(name)[
                0
            ]  # remove ext because it can be an archive type

            language = Language("eng")
            for img in sub.find("td", class_="tac lang").find_all("img"):
                if (
                    "hongkong" in img.attrs["src"]
                    or "china" in img.attrs["src"]
                    or "jollyroger" in img.attrs["src"]
                ):
                    language = Language("zho")
                    break
            sub_page_link = urljoin(self.server_url, a.attrs["href"])
            backup_session = copy.deepcopy(self.session)
            backup_session.headers["Referer"] = link

            subs.append(
                self.subtitle_class(language, sub_page_link, name, backup_session, year)
            )

        return subs

    def query(self, keyword, season=None, episode=None, year=None):
        params = keyword
        if season:
            params += ".S{season:02d}".format(season=season)
        elif year:
            params += " {:4d}".format(year)

        logger.debug("Searching subtitles %r", params)
        subtitles = []
        search_link = self.server_url + text_type(self.search_url).format(params)

        r = self.session.get(search_link, timeout=30)
        r.raise_for_status()

        if not r.content:
            logger.debug("No data returned from provider")
            return []

        html = r.content.decode("utf-8", "ignore")
        # parse window location
        pattern = r"url\s*=\s*'([^']*)'\s*\+\s*url"
        parts = re.findall(pattern, html)
        redirect_url = search_link
        while parts:
            parts.reverse()
            redirect_url = urljoin(self.server_url, "".join(parts))
            r = self.session.get(redirect_url, timeout=30)
            html = r.content.decode("utf-8", "ignore")
            parts = re.findall(pattern, html)
        logger.debug("search url located: " + redirect_url)

        soup = ParserBeautifulSoup(
            r.content.decode("utf-8", "ignore"), ["lxml", "html.parser"]
        )

        # non-shooter result page
        if soup.find("div", {"class": "item"}):
            logger.debug("enter a non-shooter page")
            for item in soup.find_all("div", {"class": "item"}):
                title_a = item.find("p", class_="tt clearfix").find("a")
                subs_year = year
                if season:
                    # episode year in zimuku is the season's year not show's year
                    actual_subs_year = re.findall(r"\d{4}", title_a.text) or None
                    if actual_subs_year:
                        subs_year = int(actual_subs_year[0]) - season + 1
                    title = title_a.text
                    season_cn1 = re.search("第(.*)季", title)
                    if not season_cn1:
                        season_cn1 = "一"
                    else:
                        season_cn1 = season_cn1.group(1).strip()
                    season_cn2 = num_to_cn(str(season))
                    if season_cn1 != season_cn2:
                        continue
                episode_link = self.server_url + title_a.attrs["href"]
                new_subs = self._parse_episode_page(episode_link, subs_year)
                subtitles += new_subs

        # NOTE: shooter result pages are ignored due to the existence of assrt provider

        return subtitles

    def list_subtitles(self, video, languages):
        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
        elif isinstance(video, Movie):
            titles = [video.title] + video.alternative_titles
        else:
            titles = []

        subtitles = []
        # query for subtitles with the show_id
        for title in titles:
            if isinstance(video, Episode):
                subtitles += [
                    s
                    for s in self.query(
                        title,
                        season=video.season,
                        episode=video.episode,
                        year=video.year,
                    )
                    if s.language in languages
                ]
            elif isinstance(video, Movie):
                subtitles += [
                    s
                    for s in self.query(title, year=video.year)
                    if s.language in languages
                ]

        return subtitles

    def download_subtitle(self, subtitle):
        def _get_archive_dowload_link(session, sub_page_link):
            r = session.get(sub_page_link)
            bs_obj = ParserBeautifulSoup(
                r.content.decode("utf-8", "ignore"), ["html.parser"]
            )
            down_page_link = bs_obj.find("a", {"id": "down1"}).attrs["href"]
            down_page_link = urljoin(sub_page_link, down_page_link)
            r = session.get(down_page_link)
            bs_obj = ParserBeautifulSoup(
                r.content.decode("utf-8", "ignore"), ["html.parser"]
            )
            download_link = bs_obj.find("a", {"rel": "nofollow"})
            download_link = download_link.attrs["href"]
            download_link = urljoin(sub_page_link, download_link)
            return download_link

        # download the subtitle
        logger.info("Downloading subtitle %r", subtitle)
        self.session = subtitle.session
        download_link = _get_archive_dowload_link(self.session, subtitle.page_link)
        r = self.session.get(download_link, timeout=30)
        r.raise_for_status()
        filename = r.headers["Content-Disposition"]

        if not r.content:
            logger.debug("Unable to download subtitle. No data returned from provider")
            return

        archive_stream = io.BytesIO(r.content)
        archive = None
        if rarfile.is_rarfile(archive_stream):
            logger.debug("Identified rar archive")
            if ".rar" not in filename:
                logger.debug(
                    ".rar should be in the downloaded file name: {}".format(filename)
                )
                return
            archive = rarfile.RarFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Identified zip archive")
            if ".zip" not in filename:
                logger.debug(
                    ".zip should be in the downloaded file name: {}".format(filename)
                )
                return
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        else:
            is_sub = ""
            for sub_ext in SUBTITLE_EXTENSIONS:
                if sub_ext in filename:
                    is_sub = sub_ext
                    break
            if not is_sub:
                logger.debug(
                    "unknown subtitle ext int downloaded file name: {}".format(filename)
                )
                return
            logger.debug("Identified {} file".format(is_sub))
            subtitle_content = r.content

        if subtitle_content:
            subtitle.content = fix_line_ending(subtitle_content)
        else:
            logger.debug("Could not extract subtitle from %r", archive)


def _get_subtitle_from_archive(archive):
    extract_subname, max_score = "", -1

    for subname in archive.namelist():
        # discard hidden files
        if os.path.split(subname)[-1].startswith("."):
            continue

        # discard non-subtitle files
        if not subname.lower().endswith(SUBTITLE_EXTENSIONS):
            continue

        # prefer ass/ssa subtitles with double languages or simplified chinese
        score = ("ass" in subname or "ssa" in subname) * 1
        if "简体" in subname or "chs" in subname or ".gb." in subname:
            score += 2
        if "繁体" in subname or "cht" in subname or ".big5." in subname:
            pass
        if "chs.eng" in subname or "chs&eng" in subname:
            score += 2
        if "中英" in subname or "简英" in subname or "双语" in subname or "简体&英文" in subname:
            score += 4
        logger.debug("subtitle {}, score: {}".format(subname, score))
        if score > max_score:
            max_score = score
            extract_subname = subname

    return archive.read(extract_subname) if max_score != -1 else None


def _extract_name(name):
    """ filter out Chinese characters from subtitle names """
    name, suffix = os.path.splitext(name)
    c_pattern = "[\u4e00-\u9fff]"
    e_pattern = "[a-zA-Z]"
    c_indices = [m.start(0) for m in re.finditer(c_pattern, name)]
    e_indices = [m.start(0) for m in re.finditer(e_pattern, name)]

    target, discard = e_indices, c_indices

    if len(target) == 0:
        return ""

    first_target, last_target = target[0], target[-1]
    first_discard = discard[0] if discard else -1
    last_discard = discard[-1] if discard else -1
    if last_discard < first_target:
        new_name = name[first_target:]
    elif last_target < first_discard:
        new_name = name[:first_discard]
    else:
        # try to find maximum continous part
        result, start, end = [0, 1], -1, 0
        while end < len(name):
            while end not in e_indices and end < len(name):
                end += 1
            if end == len(name):
                break
            start = end
            while end not in c_indices and end < len(name):
                end += 1
            if end - start > result[1] - result[0]:
                result = [start, end]
            start = end
            end += 1
        new_name = name[result[0] : result[1]]
    new_name = new_name.strip() + suffix
    return new_name


def num_to_cn(number):
    """ convert numbers(1-99) to Chinese """
    assert number.isdigit() and 1 <= int(number) <= 99

    trans_map = {n: c for n, c in zip(("123456789"), ("一二三四五六七八九"))}

    if len(number) == 1:
        return trans_map[number]
    else:
        part1 = "十" if number[0] == "1" else trans_map[number[0]] + "十"
        part2 = trans_map[number[1]] if number[1] != "0" else ""
        return part1 + part2
