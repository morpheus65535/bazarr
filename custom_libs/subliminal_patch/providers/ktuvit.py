# -*- coding: utf-8 -*-
import io
import logging
import os
import json
from requests.exceptions import JSONDecodeError

from subzero.language import Language
from guessit import guessit
from requests import Session

from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subliminal.subtitle import fix_line_ending
from subliminal import __short_version__
from subliminal.cache import SHOW_EXPIRATION_TIME, region
from subliminal.exceptions import AuthenticationError, ConfigurationError
from subliminal_patch.subtitle import guess_matches
from subliminal_patch.utils import sanitize
from subliminal.video import Episode, Movie

logger = logging.getLogger(__name__)


class KtuvitSubtitle(Subtitle):
    """Ktuvit Subtitle."""

    provider_name = "ktuvit"

    def __init__(
        self,
        language,
        hearing_impaired,
        page_link,
        series,
        season,
        episode,
        title,
        imdb_id,
        ktuvit_id,
        subtitle_id,
        release,
    ):
        super(KtuvitSubtitle, self).__init__(language, hearing_impaired, page_link)
        self.series = series
        self.season = season
        self.episode = episode
        self.title = title
        self.imdb_id = imdb_id
        self.ktuvit_id = ktuvit_id
        self.subtitle_id = subtitle_id
        self.release = release
        self.release_info = release
        self.matches = set()

    def __repr__(self):
        return "<%s [%s] %r [%s:%s]>" % (
            self.__class__.__name__,
            self.subtitle_id,
            self.page_link,
            self.language,
            self._guessed_encoding,
        )

    @property
    def id(self):
        return str(self.subtitle_id)

    def get_matches(self, video):
        # episode
        if isinstance(video, Episode):
            # series
            if video.series and (
                sanitize(self.title)
                in (
                    sanitize(name) for name in [video.series] + video.alternative_series
                )
            ):
                self.matches.add("series")
            # season
            if video.season and self.season == video.season:
                self.matches.add("season")
            # episode
            if video.episode and self.episode == video.episode:
                self.matches.add("episode")
            # imdb_id
            if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                self.matches.add("series_imdb_id")
            # guess
            self.matches |= guess_matches(video, guessit(self.release, {"type": "episode"}))
        # movie
        elif isinstance(video, Movie):
            # guess
            self.matches |= guess_matches(video, guessit(self.release, {"type": "movie"}))

            # title
            if video.title and (
                sanitize(self.title)
                in (sanitize(name) for name in [video.title] + video.alternative_titles)
            ):
                self.matches.add("title")

        return self.matches


class KtuvitProvider(Provider):
    """Ktuvit Provider."""

    languages = {Language(l) for l in ["heb"]}
    video_types = (Episode, Movie)
    server_url = "https://www.ktuvit.me/"
    sign_in_url = "Services/MembershipService.svc/Login"
    search_url = "Services/ContentProvider.svc/SearchPage_search"
    movie_info_url = "MovieInfo.aspx?ID="
    episode_info_url = "Services/GetModuleAjax.ashx?"
    request_download_id_url = "Services/ContentProvider.svc/RequestSubtitleDownload"
    download_link = "Services/DownloadFile.ashx?DownloadIdentifier="
    subtitle_class = KtuvitSubtitle
    no_subtitle_str = 'אין כתוביות'

    _tmdb_api_key = "a51ee051bcd762543373903de296e0a3"

    def __init__(self, email=None, hashed_password=None):
        if any((email, hashed_password)) and not all((email, hashed_password)):
            raise ConfigurationError("Email and Hashed Password must be specified")

        self.email = email
        self.hashed_password = hashed_password
        self.logged_in = False
        self.session = None
        self.login_cookie = None

    def initialize(self):
        self.session = Session()

        # login
        if self.email and self.hashed_password:
            logger.info("Logging in")

            data = {"request": {"Email": self.email, "Password": self.hashed_password}}

            self.session.headers["Accept-Encoding"] = "gzip"
            self.session.headers["Accept-Language"] = "en-us,en;q=0.5"
            self.session.headers["Pragma"] = "no-cache"
            self.session.headers["Cache-Control"] = "no-cache"
            self.session.headers["Content-Type"] = "application/json"
            self.session.headers["User-Agent"] = os.environ.get(
                "SZ_USER_AGENT", "Sub-Zero/2"
            )

            r = self.session.post(
                self.server_url + self.sign_in_url,
                json=data,
                allow_redirects=False,
                timeout=10,
            )

            if r.content:
                is_success = False
                try:
                    is_success = self.parse_d_response(
                        r, "IsSuccess", False, "Authentication to the provider"
                    )
                except JSONDecodeError:
                    logger.info("Failed to Login to Ktuvit")
                if not is_success:
                    error_message = ''
                    try:
                        error_message = self.parse_d_response(r, "ErrorMessage", "[None]")
                    except JSONDecodeError:
                        raise AuthenticationError(
                            "Error Logging in to Ktuvit Provider: " + str(r.content)
                        )
                    raise AuthenticationError(
                        "Error Logging in to Ktuvit Provider: " + error_message
                    )
                else:
                    cookie_split = r.headers["set-cookie"].split("Login=")
                    if len(cookie_split) != 2:
                        self.logged_in = False
                        raise AuthenticationError(
                            "Login Failed, didn't receive valid cookie in response"
                        )

                    self.login_cookie = cookie_split[1].split(";")[0]
                    logger.debug("Logged in with cookie: " + self.login_cookie)

                    self.logged_in = True

    def terminate(self):
        self.session.close()

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _search_imdb_id(self, title, year, is_movie):
        """Search the IMDB ID for the given `title` and `year`.

        :param str title: title to search for.
        :param int year: year to search for (or 0 if not relevant).
        :param bool is_movie: If True, IMDB ID will be searched for in TMDB instead of Wizdom.
        :return: the IMDB ID for the given title and year (or None if not found).
        :rtype: str

        """
        # make the search
        logger.info(
            "Searching IMDB ID for %r%r",
            title,
            "" if not year else " ({})".format(year),
        )
        category = "movie" if is_movie else "tv"
        title = title.replace("'", "")
        # get TMDB ID first
        r = self.session.get(
            "http://api.tmdb.org/3/search/{}?api_key={}&query={}{}&language=en".format(
                category,
                self._tmdb_api_key,
                title,
                "" if not year else "&year={}".format(year),
            )
        )
        r.raise_for_status()
        tmdb_results = r.json().get("results")
        if tmdb_results:
            tmdb_id = tmdb_results[0].get("id")
            if tmdb_id:
                # get actual IMDB ID from TMDB
                r = self.session.get(
                    "http://api.tmdb.org/3/{}/{}{}?api_key={}&language=en".format(
                        category,
                        tmdb_id,
                        "" if is_movie else "/external_ids",
                        self._tmdb_api_key,
                    )
                )
                r.raise_for_status()
                imdb_id = r.json().get("imdb_id")
                if imdb_id:
                    return str(imdb_id)
                else:
                    return None
        return None

    def query(
        self, title, season=None, episode=None, year=None, filename=None, imdb_id=None
    ):
        if not self.logged_in:
            logger.info("Not logged in to Ktuvit. Returning 0 results")
            return {}

        # search for the IMDB ID if needed.
        is_movie = not (season and episode)
        imdb_id = imdb_id or self._search_imdb_id(title, year, is_movie)
        if not imdb_id:
            return {}

        # search
        logger.debug("Using IMDB ID %r", imdb_id)

        query = {
            "FilmName": title,
            "Actors": [],
            "Studios": [],
            "Directors": [],
            "Genres": [],
            "Countries": [],
            "Languages": [],
            "Year": "",
            "Rating": [],
            "Page": 1,
            "SearchType": "0",
            "WithSubsOnly": False,
        }

        if not is_movie:
            query["SearchType"] = "1"

        if year:
            query["Year"] = year

        # get the list of subtitles
        logger.debug("Getting the list of subtitles")

        url = self.server_url + self.search_url
        logger.debug("Calling URL: {} with request: {}".format(url, str({"request": query})))

        r = self.session.post(url, json={"request": query}, timeout=10)
        r.raise_for_status()

        if r.content:
            results = self.parse_d_response(r, "Films", [], "Films/Series Information")
        else:
            return {}

        # loop over results
        subtitles = {}
        for result in results:
            imdb_link = result["IMDB_Link"]
            imdb_link = imdb_link[0:-1] if imdb_link.endswith("/") else imdb_link
            results_imdb_id = imdb_link.split("/")[-1]

            if results_imdb_id != imdb_id:
                logger.debug(
                    "Subtitles is for IMDB %r but actual IMDB ID is %r",
                    results_imdb_id,
                    imdb_id,
                )
                continue

            language = Language("heb")
            hearing_impaired = False
            ktuvit_id = result["ID"]
            page_link = self.server_url + self.movie_info_url + ktuvit_id

            if is_movie:
                subs = self._search_movie(ktuvit_id)
            else:
                subs = self._search_tvshow(ktuvit_id, season, episode)

            logger.debug('Got {} Subs from Ktuvit'.format(len(subs)))
            for sub in subs:
                # otherwise create it
                subtitle = KtuvitSubtitle(
                    language,
                    hearing_impaired,
                    page_link,
                    title,
                    season,
                    episode,
                    title,
                    imdb_id,
                    ktuvit_id,
                    sub["sub_id"],
                    sub["rls"],
                )
                logger.debug("Found subtitle %r", subtitle)
                subtitles[sub["sub_id"]] = subtitle

        return subtitles.values()

    def _search_tvshow(self, id, season, episode):
        subs = []

        url = (
            self.server_url
            + self.episode_info_url
            + "moduleName=SubtitlesList&SeriesID={}&Season={}&Episode={}".format(
                id, season, episode
            )
        )
        r = self.session.get(url, timeout=10)
        r.raise_for_status()
        
        if len(r.content) < 10:
            logger.debug("Too short content-length in response: [{}]. Treating as No Subtitles Found ".format(str(r.content)))
            return []

        sub_list = ParserBeautifulSoup(r.content, ["html.parser"])
        sub_rows = sub_list("tr")

        if sub_list.find("tr") and sub_list.find("tr").find("td") and sub_list.find("tr").find("td").get_text() == self.no_subtitle_str:
            logger.debug("No Subtitles Found. URL " + url)
            return subs

        for row in sub_rows:
            columns = row.find_all("td")
            sub = {"id": id}

            for index, column in enumerate(columns):
                if index == 0:
                    sub["rls"] = column.get_text().strip().split("\n")[0]
                if index == 5:
                    sub["sub_id"] = column.find("input", attrs={"data-sub-id": True})[
                        "data-sub-id"
                    ]
            
            if 'sub_id' in sub:
                subs.append(sub)
        return subs

    def _search_movie(self, movie_id):
        subs = []
        url = self.server_url + self.movie_info_url + movie_id
        r = self.session.get(url, timeout=10)
        r.raise_for_status()

        if len(r.content) < 10:
            logger.debug("Too short content-length in response: [{}]. Treating as No Subtitles Found ".format(str(r.content)))
            return []

        html = ParserBeautifulSoup(r.content, ["html.parser"])
        sub_rows = html.select("table#subtitlesList tbody > tr")

        for row in sub_rows:
            columns = row.find_all("td")
            sub = {"id": movie_id}
            for index, column in enumerate(columns):
                if index == 0:
                    sub["rls"] = column.get_text().strip().split("\n")[0]
                if index == 5:
                    sub["sub_id"] = column.find("a", attrs={"data-subtitle-id": True})[
                        "data-subtitle-id"
                    ]

            if 'sub_id' in sub:
                subs.append(sub)
        return subs

    def list_subtitles(self, video, languages):
        season = episode = None
        year = video.year
        filename = video.name

        if isinstance(video, Episode):
            titles = [video.series] + video.alternative_series
            season = video.season
            episode = video.episode
            imdb_id = video.series_imdb_id
        else:
            titles = [video.title] + video.alternative_titles
            imdb_id = video.imdb_id

        for title in titles:
            subtitles = [
                s
                for s in self.query(title, season, episode, year, filename, imdb_id)
                if s.language in languages
            ]
            if subtitles:
                return subtitles

        return []

    def download_subtitle(self, subtitle):
        if isinstance(subtitle, KtuvitSubtitle):
            download_identifier_request = {
                "FilmID": subtitle.ktuvit_id,
                "SubtitleID": subtitle.subtitle_id,
                "FontSize": 0,
                "FontColor": "",
                "PredefinedLayout": -1,
            }

            logger.debug(
                "Download Identifier Request data: "
                + str(json.dumps({"request": download_identifier_request}))
            )

            # download
            url = self.server_url + self.request_download_id_url
            r = self.session.post(
                url, json={"request": download_identifier_request}, timeout=10
            )
            r.raise_for_status()

            if r.content:
                download_identifier = self.parse_d_response(r, "DownloadIdentifier")

            url = self.server_url + self.download_link + download_identifier

            r = self.session.get(url, timeout=10)
            r.raise_for_status()

            if not r.content:
                logger.debug(
                    "Unable to download subtitle. No data returned from provider"
                )
                return

            subtitle.content = fix_line_ending(r.content)

    def parse_d_response(self, response, field, default_value=None, message=None):
        message = message if message else field

        try:
            response_content = response.json()
        except JSONDecodeError as ex:
            raise JSONDecodeError(
                "Unable to parse JSON returned while getting " + message, ex.doc, ex.pos
            )
        else:
            # kept for manual debugging when needed:
            # logger.debug("Parsing d response_content: " + str(response_content))

            if "d" in response_content:
                response_content = json.loads(response_content["d"])
                value = response_content.get(field, default_value)

                if not value and value != default_value:
                    raise JSONDecodeError(
                        "Missing " + message, str(response_content), 0
                    )
            else:
                raise JSONDecodeError(
                    "Incomplete JSON returned while getting " + message,
                    str(response_content),
                    0
                )
            return value
