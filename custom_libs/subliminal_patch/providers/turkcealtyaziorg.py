# -*- coding: utf-8 -*-
import logging
from random import randint
from datetime import datetime

from subzero.language import Language
from guessit import guessit
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.subtitle import guess_matches
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal.utils import sanitize_release_group
from subliminal.score import get_equivalent_release_groups
from subliminal.subtitle import Subtitle
from subliminal.exceptions import AuthenticationError

from http.cookies import SimpleCookie

from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
from .utils import get_archive_from_bytes

from subliminal.providers import ParserBeautifulSoup, Provider
from subliminal.video import Episode, Movie

from dateutil.relativedelta import relativedelta
from requests.cookies import RequestsCookieJar


logger = logging.getLogger(__name__)


class TurkceAltyaziOrgSubtitle(Subtitle):
    """Turkcealtyazi.org Subtitle."""

    provider_name = "turkcealtyaziorg"
    hearing_impaired_verifiable = True

    def __init__(
        self,
        language,
        page_link,
        release_info,
        uploader,
        hearing_impaired=False,
        season=None,
        episode=None,
        is_pack=False,
    ):
        super().__init__(language, hearing_impaired, page_link)
        self.season = season
        self.episode = episode
        if episode:
            self.asked_for_episode = True
        self.release_info = release_info
        self.releases = release_info
        self.is_pack = is_pack
        self.download_link = page_link
        self.uploader = uploader
        self.matches = set()
        # Currently we only search by imdb_id, so this will always be True for now
        self.imdb_match = True

    @property
    def id(self):
        id_string = self.page_link
        if self.season is not None and self.episode is not None:
            episode_string = f"S{self.season:02d}E{self.episode:02d}"
            id_string += episode_string
        return id_string

    def get_matches(self, video):
        matches = set()
        type_ = "movie" if isinstance(video, Movie) else "episode"

        # handle movies and series separately
        if type_ == "episode":
            # series
            matches.add("series")
            # season
            if video.season == self.season:
                matches.add("season")
            # episode
            if video.episode == self.episode:
                matches.add("episode")
            # imdb
            if self.imdb_match:
                matches.add("series_imdb_id")
        else:
            # imdb
            if self.imdb_match:
                matches.add("imdb_id")

        # release_group
        if (
            video.release_group
            and self.release_info
            and any(
                r in sanitize_release_group(self.release_info)
                for r in get_equivalent_release_groups(
                    sanitize_release_group(video.release_group)
                )
            )
        ):
            matches.add("release_group")

        # other properties
        matches |= guess_matches(video, guessit(self.release_info, {"type": type_}))

        self.matches = matches

        return matches


class TurkceAltyaziOrgProvider(Provider, ProviderSubtitleArchiveMixin):
    """Turkcealtyazi.org Provider."""

    languages = {Language.fromalpha3b("tur"), Language.fromalpha3b("eng")}
    video_types = (Episode, Movie)
    server_url = "https://turkcealtyazi.org"
    server_dl_url = f"{server_url}/ind"
    subtitle_class = TurkceAltyaziOrgSubtitle

    custom_identifiers = {
        # Rip Types
        "cps c1": "DVDRip",
        "cps c2": "HDRip",
        "cps c3": "TVRip",
        "rps r1": "HD",
        "rps r2": "DVDRip",
        "rps r3": "DVDScr",
        "rps r4": "R5",
        "rps r5": "CAM",
        "rps r6": "WEBRip",
        "rps r7": "BDRip",
        "rps r8": "WEB-DL",
        "rps r9": "HDRip",
        "rps r10": "HDTS",
        "rps r12": "BluRay",
        "rip1": "DVDRip",
        "rip2": "DVDScr",
        "rip3": "WEBRip",
        "rip4": "BDRip",
        "rip5": "BRRip",
        "rip6": "CAM",
        "rip7": "HD",
        "rip8": "R5",
        "rip9": "WEB-DL",
        "rip10": "HDRip",
        "rip11": "HDTS",
        # Languages
        "flagtr": "tur",
        "flagen": "eng",
        "flages": "spa",
        "flagfr": "fra",
        "flagger": "ger",
        "flagita": "ita",
        "flagunk": "unknown",
        # Turkish time granularity
        "dakika": "minutes",
        "saat": "hours",
        "gün": "days",
        "hafta": "weeks",
        "ay": "months",
        "yıl": "years",
    }

    def __init__(self, cookies=None, user_agent=None):
        self.session = None
        self.cookies = cookies
        self.user_agent = user_agent

    def initialize(self):
        self.session = RetryingCFSession()
        if self.user_agent and self.user_agent != "":
            self.session.headers["User-Agent"] = self.user_agent
        else:
            self.session.headers["User-Agent"] = AGENT_LIST[
                randint(0, len(AGENT_LIST) - 1)
            ]
        self.session.headers["Referer"] = self.server_url

        if self.cookies and self.cookies != "":
            self.session.cookies = RequestsCookieJar()
            simple_cookie = SimpleCookie()
            simple_cookie.load(self.cookies)

            for k, v in simple_cookie.items():
                self.session.cookies.set(k, v.value)

        rr = self.session.get(self.server_url, allow_redirects=False, timeout=10)
        if rr.status_code == 403:
            logger.info("Cookies expired")
            raise AuthenticationError("Cookies with User Agent are not valid anymore")

    def terminate(self):
        self.session.close()

    def list_subtitles(self, video, languages):
        imdbId = None
        subtitles = []

        if isinstance(video, Episode):
            imdbId = video.series_imdb_id
        else:
            imdbId = video.imdb_id

        if not imdbId:
            logger.debug("No imdb number available to search with provider")
            return subtitles

        # query for subtitles with the imdbId
        if isinstance(video, Episode):
            subtitles = self.query(
                video, languages, imdbId, season=video.season, episode=video.episode
            )
        else:
            subtitles = self.query(video, languages, imdbId)

        return subtitles

    def query(self, video, languages, imdb_id, season=None, episode=None):
        logger.debug("Searching subtitles for %r", imdb_id)
        subtitles = []
        type_ = "movie" if isinstance(video, Movie) else "episode"
        search_link = f"{self.server_url}/find.php?cat=sub&find={imdb_id}"

        r = self.session.get(search_link, timeout=30)

        # 404 should be returned if the imdb_id was not found, but the site returns 200 but just in case
        if r.status_code == 404:
            logger.debug("IMDB id {} not found on turkcealtyaziorg".format(imdb_id))
            return subtitles

        if r.status_code != 200:
            r.raise_for_status()

        soup_page = ParserBeautifulSoup(
            r.content.decode("utf-8", "ignore"), ["html.parser"]
        )

        # 404 Error is in the meta description if the imdb_id was not found
        meta_tag = soup_page.find("meta", {"name": "description"})
        if not meta_tag or "404 Error" in meta_tag.attrs.get("content", ""):
            logger.debug("IMDB id %s not found on turkcealtyaziorg", imdb_id)
            return subtitles
        try:
            if type_ == "movie":
                entries = soup_page.select(
                    "div.altyazi-list-wrapper > div > div.altsonsez2"
                )
            else:
                entries = soup_page.select(
                    f"div.altyazi-list-wrapper > div > div.altsonsez1.sezon_{season}"
                )

            for item in entries:
                is_pack = False

                sub_page_link = (
                    self.server_url
                    + item.select("div.alisim > div.fl > a")[0].attrs["href"]
                )

                sub_language = self.custom_identifiers.get(
                    item.select("div.aldil > span")[0].attrs["class"][0]
                )
                sub_language = Language.fromalpha3b(sub_language)
                if type_ == "episode":
                    sub_season, sub_episode = [
                        x.text for x in item.select("div.alcd")[0].find_all("b")
                    ]

                    sub_season = int(sub_season)
                    try:
                        sub_episode = int(sub_episode)
                    except ValueError:
                        is_pack = True

                sub_uploader_container = item.select("div.alcevirmen")[0]
                if sub_uploader_container.text != "":
                    sub_uploader = sub_uploader_container.text.strip()
                else:
                    sub_uploader = self.custom_identifiers.get(
                        " ".join(sub_uploader_container.find("span").attrs["class"])
                    )

                _sub_fps = item.select("div.alfps")[0].text
                _sub_download_count = item.select("div.alindirme")[0].text

                sub_release_info_list = list()
                sub_rip_container = item.select("div.ta-container > div.ripdiv")[0]

                for sub_rip in sub_rip_container.find_all("span"):
                    sub_release_info_list.append(
                        self.custom_identifiers.get(" ".join(sub_rip.attrs["class"]))
                    )
                sub_release_info_list.extend(
                    x.strip() for x in sub_rip_container.text.strip().split("/")
                )
                sub_release_info = ",".join(sub_release_info_list)

                sub_hearing_impaired = bool(
                    sub_rip_container.find("img", {"src": "/images/isitme.png"})
                )

                sub_released_at_string = item.select("div.ta-container > div.datediv")[
                    0
                ].text
                _sub_released_at = self.get_approximate_time(sub_released_at_string)

                if (sub_language in languages) and (
                    type_ == "movie"
                    or (sub_season == season)
                    and (is_pack or sub_episode == episode)
                ):
                    subtitle = self.subtitle_class(
                        sub_language,
                        sub_page_link,
                        sub_release_info,
                        sub_uploader,
                        hearing_impaired=sub_hearing_impaired,
                        season=sub_season if type_ == "episode" else None,
                        episode=(
                            (episode if is_pack else sub_episode)
                            if type_ == "episode"
                            else None
                        ),
                        is_pack=bool(is_pack),
                    )

                    logger.debug("Found subtitle %r", subtitle)
                    subtitles.append(subtitle)
        except Exception as e:
            logging.debug(e)

        return subtitles

    def download_subtitle(self, subtitle: TurkceAltyaziOrgSubtitle):
        if not isinstance(subtitle, TurkceAltyaziOrgSubtitle):
            return
        page_link = subtitle.page_link
        sub_page_resp = self.session.get(page_link, timeout=30)
        dl_page = ParserBeautifulSoup(
            sub_page_resp.content.decode("utf-8", "ignore"),
            ["html.parser"],
        )

        idid = dl_page.find("input", {"name": "idid"}).get("value")
        altid = dl_page.find("input", {"name": "altid"}).get("value")
        sidid = dl_page.find("input", {"name": "sidid"}).get("value")

        referer = page_link.encode("utf-8")

        dl_resp = self.session.post(
            self.server_dl_url,
            data={
                "idid": idid,
                "altid": altid,
                "sidid": sidid,
            },
            headers={"Referer": referer},
            timeout=10,
        )

        if not dl_resp.content:
            logger.error("Unable to download subtitle. No data returned from provider")

        archive = get_archive_from_bytes(dl_resp.content)
        subtitle.content = self.get_subtitle_from_archive(subtitle, archive)

    def get_approximate_time(self, time_string):
        time_string = time_string.strip().replace(" önce", "")
        count, granularity = time_string.split(" ")
        granularity = self.custom_identifiers[granularity]
        count = int(count)
        return (datetime.now() - relativedelta(**{granularity: count})).isoformat()
