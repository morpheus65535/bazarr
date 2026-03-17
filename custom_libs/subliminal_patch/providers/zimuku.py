# -*- coding: utf-8 -*-
from __future__ import absolute_import
import base64
import io
import logging
import os
import zipfile
import re
import copy
from PIL import Image

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

import rarfile
from babelfish import language_converters
from subzero.language import Language
from guessit import guessit
from requests import Session
from six import text_type
from random import randint, randrange

from python_anticaptcha import AnticaptchaClient, ImageToTextTask
from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.providers import Provider
from subliminal.subtitle import (
    SUBTITLE_EXTENSIONS,
    fix_line_ending
)
from subliminal_patch.subtitle import (
    Subtitle,
    guess_matches
)
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)

language_converters.register('zimuku = subliminal_patch.converters.zimuku:zimukuConverter')

supported_languages = list(language_converters['zimuku'].to_zimuku.keys())


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
        self.matches = set()

    @property
    def id(self):
        return self.page_link

    def get_matches(self, video):
        if video.year == self.year:
            self.matches.add('year')

        # episode
        if isinstance(video, Episode):
            info = guessit(self.version, {"type": "episode"})
            # other properties
            self.matches |= guess_matches(video, info)

            # add year to matches if video doesn't have a year but series, season and episode are matched
            if not video.year and all(item in self.matches for item in ['series', 'season', 'episode']):
                self.matches |= {'year'}
        # movie
        elif isinstance(video, Movie):
            # other properties
            self.matches |= guess_matches(video, guessit(self.version, {"type": "movie"}))

        return self.matches


def string_to_hex(s):
    val = ""
    for i in s:
        val += hex(ord(i))[2:]
    return val


class ZimukuProvider(Provider):
    """Zimuku Provider."""

    languages = {Language(*l) for l in supported_languages}
    video_types = (Episode, Movie)
    logger.info(str(supported_languages))

    server_url = "https://srtku.com"
    search_url = "/search?q={}"

    subtitle_class = ZimukuSubtitle

    def __init__(self):
        self.session = None

    verify_token = ""
    code = ""
    location_re = re.compile(
        r'self\.location = "(.*)" \+ stringToHex\(')
    verification_image_re = re.compile(r'<img.*?src="data:image/bmp;base64,(.*?)".*?>')

    def yunsuo_bypass(self, url, *args, **kwargs):
        def parse_verification_image(image_content: str):

            def bmp_to_image(base64_str, img_type='png'):
                img_data = base64.b64decode(base64_str)
                img = Image.open(io.BytesIO(img_data))
                img = img.convert("RGB")
                img_fp = io.BytesIO()
                img.save(img_fp, img_type)
                img_fp.seek(0)
                return img_fp

            fp = bmp_to_image(image_content)
            task = ImageToTextTask(fp)
            client = AnticaptchaClient(os.environ.get('ANTICAPTCHA_ACCOUNT_KEY'))
            job = client.createTask(task)
            job.join()
            return job.get_captcha_text()

        i = -1
        while True:
            i += 1
            r = self.session.get(url, *args, **kwargs)
            if r.status_code == 404:
                # mock js script logic
                tr = self.location_re.findall(r.text)
                verification_image = self.verification_image_re.findall(r.text)
                if len(verification_image):
                    self.code = parse_verification_image(verification_image[0])
                else:
                    self.code = f"{randrange(800, 1920)},{randrange(600, 1080)}"
                self.session.cookies.set("srcurl", string_to_hex(r.url))
                if tr:
                    verify_resp = self.session.get(
                        urljoin(self.server_url, tr[0] + string_to_hex(self.code)), allow_redirects=False)
                    if verify_resp.status_code == 302 \
                            and self.session.cookies.get("security_session_verify") is not None:
                        pass
                    continue
            if len(self.location_re.findall(r.text)) == 0:
                self.verify_token = string_to_hex(self.code)
                return r

    def initialize(self):
        self.session = Session()
        self.session.headers["User-Agent"] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        self.session.close()

    def _parse_episode_page(self, link, year):
        r = self.yunsuo_bypass(link)
        bs_obj = ParserBeautifulSoup(
            r.content.decode("utf-8", "ignore"), ["html.parser"]
        )
        subs_body = bs_obj.find("tbody")
        subs = []
        for sub in subs_body.find_all("tr"):
            a = sub.find("a")
            name = _extract_name(a.text)
            name = os.path.splitext(name)[
                0
            ]  # remove ext because it can be an archive type

            language = Language("eng")
            language_list = []

            for img in sub.find("td", class_="tac lang").find_all("img"):
                if (
                        "china" in img.attrs["src"]
                        and "hongkong" in img.attrs["src"]
                ):
                    logger.debug("language:" + str(language))
                    
                    language = Language("zho").add(Language('zho', 'TW', None))
                    language_list.append(language)
                elif (
                        "china" in img.attrs["src"]
                        or "jollyroger" in img.attrs["src"]
                ):
                    logger.debug("language chinese simplified found: " + str(language))

                    language = Language("zho")
                    language_list.append(language)
                elif "hongkong" in img.attrs["src"]:
                    logger.debug("language chinese traditional found: " + str(language))

                    language = Language('zho', 'TW', None)
                    language_list.append(language)
            sub_page_link = urljoin(self.server_url, a.attrs["href"])
            backup_session = copy.deepcopy(self.session)
            backup_session.headers["Referer"] = link

            # Mark each language of the subtitle as its own subtitle, and add it to the list, when handling archives or subtitles
            # with multiple languages to ensure each language is identified as its own subtitle since they are the same archive file
            # but will have its own file when downloaded and extracted.
            for language in language_list:
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
        search_link = urljoin(self.server_url, text_type(self.search_url).format(params))

        r = self.yunsuo_bypass(search_link, timeout=30)
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
                episode_link = urljoin(self.server_url, title_a.attrs["href"])
                new_subs = self._parse_episode_page(episode_link, subs_year)
                subtitles += new_subs

        # NOTE: shooter result pages are ignored due to the existence of zimuku provider

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
        def _get_archive_download_link(yunsuopass, sub_page_link):
            res = yunsuopass(sub_page_link)
            bs_obj = ParserBeautifulSoup(
                res.content.decode("utf-8", "ignore"), ["html.parser"]
            )
            down_page_link = bs_obj.find("a", {"id": "down1"}).attrs["href"]
            down_page_link = urljoin(sub_page_link, down_page_link)
            res = yunsuopass(down_page_link)
            bs_obj = ParserBeautifulSoup(
                res.content.decode("utf-8", "ignore"), ["html.parser"]
            )
            return urljoin(sub_page_link, bs_obj.find("a", {"rel": "nofollow"}).attrs["href"])

        # download the subtitle
        logger.info("Downloading subtitle %r", subtitle)
        download_link = _get_archive_download_link(self.yunsuo_bypass, subtitle.page_link)
        r = self.yunsuo_bypass(download_link, headers={'Referer': subtitle.page_link}, timeout=30)
        r.raise_for_status()
        try:
            filename = r.headers["Content-Disposition"].lower()
        except KeyError:
            logger.debug("Unable to parse subtitles filename. Dropping this subtitles.")
            return

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

        # prefer ass/ssa/srt subtitles with double languages or simplified/traditional chinese
        score = ("ass" in subname or "ssa" in subname or "srt" in subname) * 1
        if "简体" in subname or "chs" in subname or ".gb." in subname:
            score += 2
        if "繁体" in subname or "cht" in subname or ".big5." in subname:
            score += 2
        if "chs.eng" in subname or "chs&eng" in subname or "cht.eng" in subname or "cht&eng" in subname:
            score += 2
        if "中英" in subname or "简英" in subname or "繁英" in subname or "双语" in subname or "简体&英文" in subname or "繁体&英文" in subname:
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
        new_name = name[result[0]: result[1]]
    new_name = new_name.strip() + suffix
    return new_name


def num_to_cn(number):
    """ convert numbers(1-99) to Chinese """
    assert number.isdigit() and 1 <= int(number) <= 99

    trans_map = {n: c for n, c in zip("123456789", "一二三四五六七八九")}

    if len(number) == 1:
        return trans_map[number]
    else:
        part1 = "十" if number[0] == "1" else trans_map[number[0]] + "十"
        part2 = trans_map[number[1]] if number[1] != "0" else ""
        return part1 + part2
