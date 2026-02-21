# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import io

from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from guessit import guessit
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal_patch.exceptions import TooManyRequests
from subliminal.video import Episode, Movie
from subzero.language import Language
from subliminal.exceptions import ServiceUnavailable

import gzip
import random
from time import sleep
from xml.etree import ElementTree

logger = logging.getLogger(__name__)


class BSPlayerSubtitle(Subtitle):
    """BSPlayer Subtitle."""
    provider_name = "bsplayer"
    hash_verifiable = True

    def __init__(self, language, filename, subtype, video, link, subid):
        super(BSPlayerSubtitle, self).__init__(language)
        self.filename = filename
        self.page_link = link
        self.subtype = subtype
        self.video = video
        self.subid = subid
        self.release_info = filename
        self.matches = set()

    @property
    def id(self):
        return self.subid

    def get_matches(self, video):
        self.matches |= guess_matches(video, guessit(self.filename))

        # episode
        if isinstance(video, Episode):
            # already matched in search query
            self.matches.update(["title", "series", "season", "episode", "year"])

        # movie
        elif isinstance(video, Movie):
            # already matched in search query
            self.matches.update(["title", "year"])

        self.matches.add("hash")

        return self.matches


class BSPlayerProvider(Provider):
    """BSPlayer Provider."""

    # fmt: off
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'bul', 'ces', 'dan', 'deu', 'ell', 'eng', 'fin', 'fra', 'hun', 'ita', 'jpn', 'kor', 'nld', 'pol', 'por',
        'ron', 'rus', 'spa', 'swe', 'tur', 'ukr', 'zho'
    ]}
    video_types = (Episode, Movie)
    SEARCH_THROTTLE = 8
    hash_verifiable = True
    # fmt: on

    # batantly based on kodi's bsplayer plugin
    # also took from BSPlayer-Subtitles-Downloader
    def __init__(self):
        self.initialize()

    def initialize(self):
        self.session = Session()
        # Try to avoid bsplayer throttling increasing retries time (0, 4, 6, 8, 10)
        retry = Retry(connect=5, backoff_factor=2)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)

        # commented out this part to prevent usage of this provider and return no subtitles
        # self.search_url = self.get_sub_domain()
        # self.login()

    def terminate(self):
        self.session.close()
        self.logout()

    def api_request(self, func_name="logIn", params="", tries=5):
        headers = {
            "User-Agent": "BSPlayer/2.x (1022.12360)",
            "Content-Type": "text/xml; charset=utf-8",
            "Connection": "close",
            "SOAPAction": '"http://api.bsplayer-subtitles.com/v1.php#{func_name}"'.format(
                func_name=func_name
            ),
        }
        data = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ns1="{search_url}">'
            '<SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            "<ns1:{func_name}>{params}</ns1:{func_name}></SOAP-ENV:Body></SOAP-ENV:Envelope>"
        ).format(search_url=self.search_url, func_name=func_name, params=params)
        logger.debug("Sending request: %s." % func_name)
        for i in iter(range(tries)):
            try:
                self.session.headers.update(headers.items())
                res = self.session.post(self.search_url, data)
                return ElementTree.fromstring(res.text.strip())

            except Exception as ex:
                logger.error(f"Exception parsing response: {ex}")
                if func_name == "logIn":
                    self.search_url = self.get_sub_domain()

                sleep(1)

        raise TooManyRequests(f"Too many retries: {tries}")

    def login(self):
        # Setting attribute here as initialize() will reset it
        if hasattr(self, "token"):
            logger.debug("Token already met. Skipping logging")
            return True

        root = self.api_request(
            func_name="logIn",
            params=(
                "<username></username>"
                "<password></password>"
                "<AppID>BSPlayer v2.67</AppID>"
            ),
        )
        res = root.find(".//return")
        # avoid AttributeError
        if not res:
            return False

        if res.find("status").text == "OK":
            self.token = res.find("data").text
            logger.debug("Logged In Successfully.")
            return True
        return False

    def logout(self):
        # If already logged out / not logged in
        # if not self.token:
        #    return True
        if not hasattr(self, "token"):
            logger.debug("Already logged out")
            return True

        root = self.api_request(
            func_name="logOut",
            params="<handle>{token}</handle>".format(token=self.token),
        )
        res = root.find(".//return")
        self.token = None

        # avoid AttributeError
        if not res:
            logger.debug("Root logout returned None")
            return False

        if res.find("status").text == "OK":
            logger.debug("Logged Out Successfully.")
            return True

        return False

    def query(self, video, video_hash, language):
        if not self.login():
            logger.debug("Token not found. Can't perform query")
            return []

        if isinstance(language, (tuple, list, set)):
            # language_ids = ",".join(language)
            # language_ids = 'spa'
            language_ids = ",".join(sorted(l.opensubtitles for l in language))

        if video.imdb_id is None:
            imdbId = "*"
        else:
            imdbId = video.imdb_id
        sleep(self.SEARCH_THROTTLE)
        root = self.api_request(
            func_name="searchSubtitles",
            params=(
                "<handle>{token}</handle>"
                "<movieHash>{movie_hash}</movieHash>"
                "<movieSize>{movie_size}</movieSize>"
                "<languageId>{language_ids}</languageId>"
                "<imdbId>{imdbId}</imdbId>"
            ).format(
                token=self.token,
                movie_hash=video_hash,
                movie_size=video.size,
                language_ids=language_ids,
                imdbId=imdbId,
            ),
        )
        res = root.find(".//return/result")

        if not res:
            logger.debug("No subtitles found")
            return []

        status = res.find("status").text
        if status != "OK":
            logger.debug(f"No subtitles found (bad status: {status})")
            return []

        items = root.findall(".//return/data/item")
        subtitles = []
        if items:
            logger.debug("Subtitles Found.")
            for item in items:
                subID = item.find("subID").text
                subDownloadLink = item.find("subDownloadLink").text
                subLang = Language.fromopensubtitles(item.find("subLang").text)
                subName = item.find("subName").text
                subFormat = item.find("subFormat").text
                subtitles.append(
                    BSPlayerSubtitle(
                        subLang, subName, subFormat, video, subDownloadLink, subID
                    )
                )
        return subtitles

    def list_subtitles(self, video, languages):
        return []
        # commented out this part to prevent usage of this provider and return no subtitles
        # return self.query(video, video.hashes["bsplayer"], languages)

    def get_sub_domain(self):
        # API_URL_TEMPLATE = None
        # session = Session()
        # s1-9, s101-109

        # Don't test again
        # fixme: Setting attribute here as initialize() may reset it (maybe
        # there's a more elegant way?)
        if hasattr(self, "API_URL_TEMPLATE"):
            logger.debug(f"Working subdomain already met: {self.API_URL_TEMPLATE}")
            return self.API_URL_TEMPLATE
        else:
            self.API_URL_TEMPLATE = None

        # fmt: off
        SUB_DOMAINS = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8',
                       's101', 's102', 's103', 's104', 's105', 's106', 's107', 's108', 's109']
        # fmt: on
        random.shuffle(SUB_DOMAINS)
        # Limit to 8 tests
        for domain in SUB_DOMAINS[:8]:
            TEST_URL = "http://{}.api.bsplayer-subtitles.com".format(domain)
            try:
                logging.debug("Testing BSplayer sub-domain {}".format(TEST_URL))
                res = self.session.get(TEST_URL, timeout=3)
            except:
                continue
            else:
                res.raise_for_status()

                if res.status_code == 200:
                    logger.debug(f"Found working subdomain: {domain}")
                    self.API_URL_TEMPLATE = (
                        "http://{}.api.bsplayer-subtitles.com/v1.php".format(domain)
                    )
                    break
                else:
                    sleep(1)
                    continue

        if self.API_URL_TEMPLATE:
            return self.API_URL_TEMPLATE

        raise ServiceUnavailable("No API URL template was found")

    def download_subtitle(self, subtitle):
        # session = Session()
        _addheaders = {"User-Agent": "Mozilla/4.0 (compatible; Synapse)"}
        self.session.headers.update(_addheaders)
        res = self.session.get(subtitle.page_link)
        if res:
            if res.text == "500":
                raise ServiceUnavailable("Error 500 on server")

            with gzip.GzipFile(fileobj=io.BytesIO(res.content)) as gf:
                subtitle.content = gf.read()
                subtitle.normalize()

            return subtitle
        raise ServiceUnavailable("Problems conecting to the server")
