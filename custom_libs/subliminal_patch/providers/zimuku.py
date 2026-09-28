# -*- coding: utf-8 -*-
from __future__ import absolute_import
import base64
import io
import logging
import os
import zipfile
import re
import copy
from py7zr import SevenZipFile, is_7zfile
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

from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.pitcher import pitchers
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


class SevenZipArchive(object):
    def __init__(self, stream_or_bytes):
        if isinstance(stream_or_bytes, (bytes, bytearray)):
            stream = io.BytesIO(stream_or_bytes)
        else:
            stream = stream_or_bytes
            stream.seek(0)
        self._archive = SevenZipFile(stream, mode="r")
        self._files = self._archive.readall()

    def namelist(self):
        return list(self._files.keys())

    def read(self, name):
        bio = self._files.get(name)
        if bio is not None:
            bio.seek(0)
            return bio.read()
        return None

    def close(self):
        try:
            self._archive.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ---------------------------------------------------------------------------
# Yunsuo WAF CAPTCHA Solver Constants
# ---------------------------------------------------------------------------
# Yunsuo CAPTCHA always renders exactly 5 digits
_CAPTCHA_DIGIT_COUNT = 5

# Horizontal width (in pixels) allocated for each digit slot (e.g. 0-19, 20-39, etc.)
_CAPTCHA_SLOT_WIDTH = 20

# Minimum expected image width (standard Yunsuo CAPTCHA is ~100px)
_CAPTCHA_MIN_WIDTH = 90

# Minimum expected image height (standard Yunsuo CAPTCHA is ~30px)
_CAPTCHA_MIN_HEIGHT = 22

# Vertical pixel row range [6, 22) scanned for digit strokes, avoiding top/bottom border noise
_CAPTCHA_SCAN_Y_RANGE = range(6, 22)

# Minimum green channel value (0-255) required for a pixel to be considered foreground
_GREEN_MIN_INTENSITY = 80

# Minimum difference (G - R and G - B) required to filter out neutral/gray noise lines
_GREEN_DOMINANCE_THRESHOLD = 30

# Maximum allowed bitwise pixel mismatches across a 14-row template before rejecting a digit
_MAX_PIXEL_MISMATCH_THRESHOLD = 15

# Maximum number of challenge attempts in the bypass loop to prevent hanging
_MAX_YUNSUO_RETRIES = 6

# ---------------------------------------------------------------------------
# Yunsuo BMP CAPTCHA Digit Bitmaps (14 rows high, 7-9 cols wide)
# ---------------------------------------------------------------------------
# Each digit is mapped to (width, [14 row bitmasks]) where the most significant
# bit (w - 1) is the leftmost pixel and bit 0 is the rightmost.
#
# To inspect or visualize these bitmasks as ASCII art, run in terminal:
#
#   python3 -c '
#   from subliminal_patch.providers.zimuku import _DIGIT_TEMPLATES
#   for digit, (w, rows) in _DIGIT_TEMPLATES.items():
#       print(f"=== Digit {digit} ===")
#       for r in rows:
#           print("".join("#" if (r >> (w - 1 - x)) & 1 else " " for x in range(w)))
#       print()
#   '
# ---------------------------------------------------------------------------
_DIGIT_TEMPLATES = {
    "0": (8, (0x3C, 0x7E, 0x66, 0xC3, 0xC3, 0xC3, 0xDB, 0xCB, 0xC3, 0xC3, 0xC3, 0x66, 0x7E, 0x3C)),
    "1": (7, (0x18, 0x78, 0x68, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x7F, 0x7F)),
    "2": (8, (0x7C, 0xFE, 0x87, 0x03, 0x03, 0x03, 0x07, 0x06, 0x0C, 0x18, 0x30, 0x60, 0xFF, 0xFF)),
    "3": (8, (0x7C, 0xFE, 0x87, 0x03, 0x03, 0x07, 0x1E, 0x1E, 0x03, 0x03, 0x03, 0x87, 0xFE, 0x7C)),
    "4": (9, (0x01C, 0x01C, 0x01C, 0x03C, 0x02C, 0x06C, 0x0CC, 0x0CC, 0x18C, 0x1FF, 0x1FF, 0x00E, 0x00C, 0x00C)),
    "5": (8, (0x7E, 0x7E, 0x60, 0x60, 0x60, 0x7E, 0x7F, 0x03, 0x03, 0x03, 0x03, 0x82, 0xFE, 0x7C)),
    "6": (8, (0x3C, 0x3E, 0x62, 0x60, 0xC0, 0xC0, 0xFE, 0xFF, 0xC3, 0xC3, 0xC3, 0x43, 0x7E, 0x3C)),
    "7": (8, (0xFF, 0xFF, 0x06, 0x06, 0x06, 0x0C, 0x0C, 0x0C, 0x08, 0x08, 0x18, 0x10, 0x18, 0x30)),
    "8": (8, (0x3C, 0x7E, 0xE7, 0xC3, 0xC3, 0x66, 0x7E, 0x7E, 0xC3, 0xC3, 0xC3, 0xC3, 0x7E, 0x3C)),
    "9": (8, (0x3C, 0x7E, 0xE6, 0xC3, 0xC3, 0xC3, 0xFF, 0x7F, 0x3B, 0x03, 0x06, 0x46, 0x7E, 0x3C)),
}


def _is_green_stroke(r, g, b):
    return (
        g > _GREEN_MIN_INTENSITY
        and (g - r > _GREEN_DOMINANCE_THRESHOLD)
        and (g - b > _GREEN_DOMINANCE_THRESHOLD)
    )


def solve_bmp_captcha(bmp_bytes):
    """Solves the 5-digit Yunsuo BMP captcha locally using template matching."""
    try:
        img = Image.open(io.BytesIO(bmp_bytes)).convert("RGB")
        width, height = img.size
        if width < _CAPTCHA_MIN_WIDTH or height < _CAPTCHA_MIN_HEIGHT:
            return None

        pixels = img.load()
        grid = [
            [_is_green_stroke(r, g, b) for r, g, b in (pixels[x, y] for x in range(width))]
            for y in range(height)
        ]

        digits = []
        for d in range(_CAPTCHA_DIGIT_COUNT):
            slot_start = d * _CAPTCHA_SLOT_WIDTH
            slot_end = (d + 1) * _CAPTCHA_SLOT_WIDTH
            pts = [(x, y) for y in _CAPTCHA_SCAN_Y_RANGE for x in range(slot_start, slot_end) if grid[y][x]]
            if not pts:
                return None
            min_x = min(x for x, _ in pts)
            min_y = min(y for _, y in pts)

            best_digit, best_diff = "?", float("inf")
            for digit, (w, rows) in _DIGIT_TEMPLATES.items():
                diff = 0
                for dy, row_mask in enumerate(rows):
                    py = min_y + dy
                    if py >= height:
                        diff += row_mask.bit_count()
                        continue
                    row_slice = grid[py][min_x:min_x + w]
                    val = 0
                    for b in row_slice:
                        val = (val << 1) | b
                    if len(row_slice) < w:
                        val <<= (w - len(row_slice))
                    diff += (val ^ row_mask).bit_count()
                if diff < best_diff:
                    best_diff = diff
                    best_digit = digit

            if best_diff > _MAX_PIXEL_MISMATCH_THRESHOLD:
                return None
            digits.append(best_digit)

        return "".join(digits) if len(digits) == _CAPTCHA_DIGIT_COUNT else None
    except Exception as e:
        logger.debug("Failed to solve BMP captcha locally: %s", e)
        return None


class ZimukuProvider(Provider):
    """Zimuku Provider."""

    languages = {Language(*l) for l in supported_languages}
    video_types = (Episode, Movie)
    logger.info(str(supported_languages))

    server_url = "https://zimuku.org"
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
            try:
                raw_bytes = base64.b64decode(image_content)
                solved = solve_bmp_captcha(raw_bytes)
                if solved:
                    logger.debug("Zimuku Yunsuo captcha solved locally: %s", solved)
                    return solved
            except Exception as e:
                logger.debug("Local captcha solver error: %s", e)

            anticaptcha_class = os.environ.get("ANTICAPTCHA_CLASS")
            if anticaptcha_class:
                pitcher_names = {
                    "AntiCaptchaProxyLess": "AntiCaptchaImageToText",
                    "CaptchaAIProxyLess": "CaptchaAIImageToText",
                }
                image_pitcher = pitcher_names.get(anticaptcha_class, "DeathByCaptchaImageToText")
                try:
                    img_fp = io.BytesIO()
                    Image.open(io.BytesIO(raw_bytes)).convert("RGB").save(img_fp, "PNG")
                    img_fp.seek(0)
                    pitcher = pitchers.get_pitcher(image_pitcher)("Zimuku", img_fp)
                    return pitcher.throw()
                except Exception as e:
                    logger.warning("External anti-captcha pitcher failed: %s", e)

            return f"{randrange(800, 1920)},{randrange(600, 1080)}"

        for _ in range(_MAX_YUNSUO_RETRIES):
            r = self.session.get(url, *args, **kwargs)
            if r.status_code == 404:
                # mock js script logic
                tr = self.location_re.findall(r.text)
                verification_image = self.verification_image_re.findall(r.text)
                if verification_image:
                    self.code = parse_verification_image(verification_image[0])
                else:
                    self.code = f"{randrange(800, 1920)},{randrange(600, 1080)}"
                self.session.cookies.set("srcurl", string_to_hex(r.url), path="/")
                if tr:
                    verify_url = urljoin(self.server_url, tr[0] + string_to_hex(self.code))
                    self.session.get(verify_url, allow_redirects=False, headers={"Referer": r.url})
                    continue
            if not self.location_re.findall(r.text):
                self.verify_token = string_to_hex(self.code)
                return r

        logger.warning("Zimuku Yunsuo bypass exceeded max retries for %s", url)
        return r

    def initialize(self):
        self.session = Session()
        self.session.headers["User-Agent"] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

    def terminate(self):
        self.session.close()

    def _parse_episode_page(self, link, year):
        if link.startswith("//"):
            link = "https:" + link
        r = self.yunsuo_bypass(link)
        bs_obj = ParserBeautifulSoup(
            r.content.decode("utf-8", "ignore"), ["html.parser"]
        )
        subs_body = bs_obj.find("tbody")
        if not subs_body:
            return []
        subs = []
        for sub in subs_body.find_all("tr"):
            a = sub.find("a")
            if not a:
                continue

            # Format check: ignore SUP subtitles (Bazarr only supports text subtitles)
            fmt_span = sub.find("span", class_="label-info")
            if fmt_span and fmt_span.get_text(strip=True).upper() == "SUP":
                logger.debug("Zimuku skipping SUP subtitle %r", a.text.strip())
                continue
            if re.search(r'\.sup(?:\.|$|\s)', a.text, re.IGNORECASE) and not any(ext in a.text.lower() for ext in ['.srt', '.ass', '.ssa']):
                logger.debug("Zimuku skipping .sup in title %r", a.text.strip())
                continue

            name = _extract_name(a.text)
            name = os.path.splitext(name)[
                0
            ]  # remove ext because it can be an archive type

            lang_td = sub.find("td", class_="tac lang")
            if not lang_td:
                continue
            lang_imgs = [img.attrs.get("src", "") for img in lang_td.find_all("img")]
            has_china = any("china" in src or "jollyroger" in src for src in lang_imgs)
            has_hk = any("hongkong" in src for src in lang_imgs)
            has_en = any("uk" in src or "en" in src for src in lang_imgs)

            language_list = []
            if has_china and has_hk:
                language_list.append(Language("zho"))
                language_list.append(Language("zho", "TW", None))
            elif has_china:
                language_list.append(Language("zho"))
            elif has_hk:
                language_list.append(Language("zho", "TW", None))

            if has_en:
                language_list.append(Language("eng"))

            if not language_list:
                language_list.append(Language("zho"))
            sub_page_link = urljoin(self.server_url, a.attrs["href"])
            if sub_page_link.startswith("//"):
                sub_page_link = "https:" + sub_page_link
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
                tt = item.find("p", class_="tt clearfix")
                if not tt:
                    continue
                title_a = tt.find("a")
                if not title_a:
                    continue
                subs_year = year
                if season:
                    # episode year in zimuku is the season's year not show's year
                    actual_subs_year = re.findall(r"\d{4}", title_a.text) or None
                    if actual_subs_year:
                        subs_year = int(actual_subs_year[0]) - season + 1
                    title = title_a.text
                    season_cn1 = re.search(r"第(.*)季", title)
                    if not season_cn1:
                        season_cn1 = "一"
                    else:
                        season_cn1 = season_cn1.group(1).strip()
                    season_cn2 = num_to_cn(str(season))
                    if season_cn1 != season_cn2:
                        continue
                episode_link = urljoin(self.server_url, title_a.attrs["href"])
                if episode_link.startswith("//"):
                    episode_link = "https:" + episode_link
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
            down1 = bs_obj.find("a", {"id": "down1"})
            if not down1 or "href" not in down1.attrs:
                logger.error("Zimuku could not find #down1 link on page %s", sub_page_link)
                return None, None
            down_page_link = urljoin(sub_page_link, down1.attrs["href"])
            if down_page_link.startswith("//"):
                down_page_link = "https:" + down_page_link

            res = yunsuopass(down_page_link)
            bs_obj = ParserBeautifulSoup(
                res.content.decode("utf-8", "ignore"), ["html.parser"]
            )
            rel_a = bs_obj.find("a", {"rel": "nofollow"})
            if not rel_a or "href" not in rel_a.attrs:
                logger.error("Zimuku could not find rel=nofollow download link on %s", down_page_link)
                return None, None
            final_down_link = urljoin(down_page_link, rel_a.attrs["href"])
            if final_down_link.startswith("//"):
                final_down_link = "https:" + final_down_link
            return final_down_link, down_page_link

        # download the subtitle
        logger.info("Downloading subtitle %r", subtitle)
        download_link, down_page_link = _get_archive_download_link(self.yunsuo_bypass, subtitle.page_link)
        if not download_link:
            logger.debug("Unable to resolve download link for %r", subtitle)
            return

        referer = down_page_link or subtitle.page_link
        r = self.yunsuo_bypass(download_link, headers={'Referer': referer}, timeout=30)
        r.raise_for_status()

        cd = r.headers.get("Content-Disposition", "")
        filename = cd.lower()

        if not r.content:
            logger.debug("Unable to download subtitle. No data returned from provider")
            return

        archive_stream = io.BytesIO(r.content)
        archive = None
        if rarfile.is_rarfile(archive_stream):
            logger.debug("Identified rar archive")
            archive = rarfile.RarFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug("Identified zip archive")
            archive = zipfile.ZipFile(archive_stream)
            subtitle_content = _get_subtitle_from_archive(archive)
        elif archive_stream.seek(0) == 0 and is_7zfile(archive_stream) or ".7z" in filename:
            logger.debug("Identified 7z archive")
            try:
                archive = SevenZipArchive(archive_stream)
                try:
                    subtitle_content = _get_subtitle_from_archive(archive)
                finally:
                    archive.close()
            except Exception as e:
                logger.warning("Failed to extract 7z archive: %s", e)
                subtitle_content = None
        else:
            is_sub = ""
            for sub_ext in SUBTITLE_EXTENSIONS:
                if sub_ext in filename:
                    is_sub = sub_ext
                    break
            if not is_sub:
                if filename.endswith(".sup") or r.content.startswith(b"PG"):
                    logger.debug("Zimuku downloaded file is unsupported .sup format: %s", filename)
                    return
                logger.debug(
                    "unknown subtitle ext in downloaded file name: {}".format(filename)
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

        # try to decode subname for score matching if gbk encoded
        name_lower = subname.lower()
        try:
            decoded_name = subname.encode('cp437').decode('gbk', 'ignore').lower()
        except Exception:
            decoded_name = name_lower

        # prefer ass/ssa/srt subtitles with double languages or simplified/traditional chinese
        score = ("ass" in name_lower or "ssa" in name_lower or "srt" in name_lower) * 1
        if "简体" in decoded_name or "chs" in name_lower or ".gb." in name_lower:
            score += 2
        if "繁体" in decoded_name or "cht" in name_lower or ".big5." in name_lower:
            score += 2
        if "chs.eng" in name_lower or "chs&eng" in name_lower or "cht.eng" in name_lower or "cht&eng" in name_lower:
            score += 2
        if any(w in decoded_name for w in ["中英", "简英", "繁英", "双语", "简体&英文", "繁体&英文"]):
            score += 4
        logger.debug("subtitle {}, score: {}".format(subname, score))
        if score > max_score:
            max_score = score
            extract_subname = subname

    if max_score != -1:
        return archive.read(extract_subname)

    sup_files = [subname for subname in archive.namelist() if subname.lower().endswith(".sup")]
    if sup_files:
        logger.debug("Zimuku archive only contains unsupported SUP/PGS files: %r", sup_files)
    return None


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
