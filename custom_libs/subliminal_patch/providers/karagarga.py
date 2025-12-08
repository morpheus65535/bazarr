# -*- coding: utf-8 -*-

import datetime
import logging

from bs4 import BeautifulSoup as bso
from requests import Session
from subliminal.cache import region as cache_region
from subliminal.exceptions import AuthenticationError
from subliminal.exceptions import ConfigurationError
from subliminal_patch.core import Movie
from subliminal_patch.providers import Provider
from subliminal_patch.providers.utils import update_matches
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language

logger = logging.getLogger(__name__)

_PROVIDER_NAME = "karagarga"
_BASE_URL = "https://karagarga.in"


class KaragargaSubtitle(Subtitle):
    provider_name = _PROVIDER_NAME
    hash_verifiable = False

    def __init__(self, language, page_link, release_info, downloads):
        super().__init__(language, page_link=page_link)

        self.release_info = release_info
        self.downloads = downloads
        self._matches = {"title", "year"}

    def get_matches(self, video):
        update_matches(self._matches, video, self.release_info, type="movie")

        return self._matches

    @property
    def id(self):
        return self.page_link


_NO_LOGGED_IN_REDIRECT = 302
_EXPIRATION_TIME = datetime.timedelta(weeks=1).total_seconds()


class KaragargaProvider(Provider):
    provider_name = _PROVIDER_NAME

    # Only english for now
    languages = {Language.fromietf("en")}

    video_types = (Movie,)
    subtitle_class = KaragargaSubtitle
    _session: Session

    def __init__(self, username: str, password: str, f_username=None, f_password=None):
        if not username or not password:
            raise ConfigurationError("Username/password not provided")

        self._username = username
        self._password = password
        self._f_username = f_username or username
        self._f_password = f_password or password

    def initialize(self):
        self._session = Session()
        self._session.headers.update(
            {"authority": "karagarga.in", "user-agent": "Bazarr"}
        )
        self._login()

    def terminate(self):
        self._session.close()

    def _login(self):
        self._login_main()
        self._login_forum()

    def _login_main(self):
        data = {
            "username": self._username,
            "password": self._password,
        }

        self._session.post(f"{_BASE_URL}/takelogin.php", data=data)

        if "pass" not in self._session.cookies:
            raise AuthenticationError("Invalid username/password")

        logger.debug("Karagarga login: OK")

    def _login_forum(self):
        params = {
            "app": "core",
            "module": "global",
            "section": "login",
            "do": "process",
        }

        data = {
            # What's the origin of this key?
            "auth_key": "880ea6a14ea49e853634fbdc5015a024",
            #
            "referer": "https://forum.karagarga.in/",
            "ips_username": self._f_username,
            "ips_password": self._f_password,
            "rememberMe": "1",
            "anonymous": "1",
        }

        self._session.post(
            "https://forum.karagarga.in/index.php", params=params, data=data
        )

        if not {"session_id", "pass_hash"}.issubset(self._session.cookies.keys()):
            raise AuthenticationError("Invalid forum username/password")

        logger.debug("Karagarga forum login: OK")

    @cache_region.cache_on_arguments(expiration_time=_EXPIRATION_TIME)
    def _cached_get(self, url, params):
        response = self._session.get(url, params=params)
        if response.status_code == _NO_LOGGED_IN_REDIRECT:
            raise AuthenticationError("Not logged in")

        return response.content

    def _search_movie(self, title, year):
        params = {"search": title, "status": "completed"}
        content = self._cached_get(f"{_BASE_URL}/pots.php", params)

        soup = bso(content, "html.parser")

        table = soup.find("table", {"cellspacing": "5"})

        if table is None:
            logger.debug("Failed to get table. Returning []")
            return []

        subtitles = []
        scans = 0

        for tr_ in table.find_all("tr"):  # type: ignore
            if "forum.karagarga" not in str(tr_):
                continue

            found_tds = tr_.find_all("td")
            if len(found_tds) != 11:
                continue

            title = found_tds[1].text

            if f"({year}" not in title:
                logger.debug("Year doesn't match: %s", title)
                continue

            logger.debug("Movie matched: %s", title)

            requested_language = found_tds[5].text
            if "English" not in requested_language:
                continue

            forum_item = found_tds[9]

            if "approved" not in str(forum_item):
                logger.debug("Non-approved subtitle: %s", title)
                continue

            try:
                forum_url = str(forum_item.find("a").get("href"))
            except AttributeError:
                continue

            if scans > 2:
                logger.debug("Forum scans limit exceeded")
                break

            subtitles += self._parse_from_forum(forum_url, Language.fromietf("en"))
            scans += 1

        return subtitles

    def _parse_from_forum(self, url, language):
        logger.debug("Scanning forum for subs: %s", url)

        content = self._cached_get(url, {})

        soup = bso(content, "html.parser")

        for post in soup.find_all("div", {"class": "post entry-content"}):
            yield from _gen_subtitles(post, language)

    def list_subtitles(self, video, languages):
        subtitles = self._search_movie(video.title, video.year)
        if not subtitles:
            return []

        subtitles.sort(key=lambda x: x.downloads, reverse=True)
        # Always return the most downloaded subtitle from the forum

        return [subtitles[0]]

    def download_subtitle(self, subtitle):
        response = self._session.get(subtitle.page_link, allow_redirects=True)
        response.raise_for_status()

        subtitle.content = response.content


def _gen_subtitles(post, language):
    seen_urls = set()

    for potential in post.select("p,li.attachment,div"):
        downloads = potential.find("span", {"class": "desc lighter"})
        if not downloads:
            continue

        try:
            download_count = int(downloads.text.split()[0].strip())
            item = [a_ for a_ in potential.find_all("a") if a_.find("strong")][0]
            release_info = item.find("strong").text
        except (AttributeError, KeyError, ValueError) as error:
            logger.debug("Error parsing post: %s", error)
            continue

        url = item.get("href")

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        subtitle = KaragargaSubtitle(language, url, release_info, download_count)
        logger.debug("Valid subtitle found: %s - %s", release_info, subtitle)
        yield subtitle
