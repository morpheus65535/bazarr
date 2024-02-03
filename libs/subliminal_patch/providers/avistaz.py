# -*- coding: utf-8 -*-
from __future__ import absolute_import
import io
import os
import logging
import time

import pycountry

from zipfile import ZipFile, is_zipfile

from guessit import guessit
from subliminal_patch.http import RetryingCFSession
import chardet
from subzero.language import Language

from subliminal_patch.providers import Provider
from subliminal_patch.providers.mixins import ProviderSubtitleArchiveMixin
from subliminal_patch.subtitle import Subtitle, guess_matches
from subliminal.providers import ParserBeautifulSoup
from subliminal.video import Episode, Movie
from subliminal.exceptions import DownloadLimitExceeded, AuthenticationError, ConfigurationError
from subliminal_patch.pitcher import pitchers, store_verification

from ..utils import sanitize
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

logger = logging.getLogger(__name__)

supported_languages_names = [
    "Abkhazian",
    "Afar",
    "Afrikaans",
    "Akan",
    "Albanian",
    "Amharic",
    "Arabic",
    "Aragonese",
    "Armenian",
    "Assamese",
    "Avaric",
    "Avestan",
    "Aymara",
    "Azerbaijani",
    "Bambara",
    "Bashkir",
    "Basque",
    "Belarusian",
    "Bengali",
    "Bihari languages",
    "Bislama",
    "Bokmål, Norwegian",
    "Bosnian",
    "Brazilian Portuguese",
    "Breton",
    "Bulgarian",
    "Burmese",
    "Cantonese",
    "Catalan",
    "Central Khmer",
    "Chamorro",
    "Chechen",
    "Chichewa",
    "Chinese",
    "Church Slavic",
    "Chuvash",
    "Cornish",
    "Corsican",
    "Cree",
    "Croatian",
    "Czech",
    "Danish",
    "Dhivehi",
    "Dutch",
    "Dzongkha",
    "English",
    "Esperanto",
    "Estonian",
    "Ewe",
    "Faroese",
    "Fijian",
    "Filipino",
    "Finnish",
    "French",
    "Fulah",
    "Gaelic",
    "Galician",
    "Ganda",
    "Georgian",
    "German",
    "Greek",
    "Guarani",
    "Gujarati",
    "Haitian",
    "Hausa",
    "Hebrew",
    "Herero",
    "Hindi",
    "Hiri Motu",
    "Hungarian",
    "Icelandic",
    "Ido",
    "Igbo",
    "Indonesian",
    "Interlingua",
    "Interlingue",
    "Inuktitut",
    "Inupiaq",
    "Irish",
    "Italian",
    "Japanese",
    "Javanese",
    "Kalaallisut",
    "Kannada",
    "Kanuri",
    "Kashmiri",
    "Kazakh",
    "Kikuyu",
    "Kinyarwanda",
    "Kirghiz",
    "Komi",
    "Kongo",
    "Korean",
    "Kuanyama",
    "Kurdish",
    "Lao",
    "Latin",
    "Latvian",
    "Limburgan",
    "Lingala",
    "Lithuanian",
    "Luba-Katanga",
    "Luxembourgish",
    "Macedonian",
    "Malagasy",
    "Malay",
    "Malayalam",
    "Maltese",
    "Mandarin",
    "Manx",
    "Maori",
    "Marathi",
    "Marshallese",
    "Mongolian",
    "Moore",
    "Nauru",
    "Navajo",
    "Ndebele, North",
    "Ndebele, South",
    "Ndonga",
    "Nepali",
    "Northern Sami",
    "Norwegian",
    "Norwegian Nynorsk",
    "Occitan (post 1500)",
    "Ojibwa",
    "Oriya",
    "Oromo",
    "Ossetian",
    "Pali",
    "Panjabi",
    "Persian",
    "Polish",
    "Portuguese",
    "Pushto",
    "Quechua",
    "Romanian",
    "Romansh",
    "Rundi",
    "Russian",
    "Samoan",
    "Sango",
    "Sanskrit",
    "Sardinian",
    "Serbian",
    "Shona",
    "Sichuan Yi",
    "Sindhi",
    "Sinhala",
    "Slovak",
    "Slovenian",
    "Somali",
    "Sotho, Southern",
    "Spanish",
    "Sundanese",
    "Swahili",
    "Swati",
    "Swedish",
    "Tagalog",
    "Tahitian",
    "Tajik",
    "Tamil",
    "Tatar",
    "Telugu",
    "Thai",
    "Tibetan",
    "Tigrinya",
    "Tongan",
    "Tsonga",
    "Tswana",
    "Turkish",
    "Turkmen",
    "Twi",
    "Uighur",
    "Ukrainian",
    "Urdu",
    "Uzbek",
    "Venda",
    "Vietnamese",
    "Volapük",
    "Walloon",
    "Welsh",
    "Western Frisian",
    "Wolof",
    "Xhosa",
    "Yiddish",
    "Yoruba",
    "Zhuang",
    "Zulu"
]


def lookup_lang(name):
    try:
        return pycountry.languages.lookup(name)
    except:
        return None


class AvistazSubtitle(Subtitle):
    """AvistaZ.to Subtitle."""
    provider_name = 'avistaz'

    def __init__(self, page_link, download_link, language, video, srt_filename, release, data, uploader):
        super().__init__(language, page_link)
        self.language = language
        self.srt_filename = srt_filename
        self.release_info = release
        self.page_link = page_link
        self.download_link = download_link
        self.data = data
        self.video = video
        self.matches = None
        self.content = None
        self.hearing_impaired = None
        self.uploader = uploader
        self.encoding = None

    @property
    def id(self):
        return self.srt_filename

    def get_matches(self, video):
        # guess additional info from data
        matches = guess_matches(video, self.data)

        # if the release group matches, the source and year is most likely correct, as well
        if "release_group" in matches:
            matches.add("source")

        if isinstance(video, Episode):
            if (video.original_series and 'year' not in self.data) or (
                    video.year and 'year' in self.data and self.data['year'] == video.year):
                matches.add('year')

        self.matches = matches
        self.data = None
        return matches


class AvistazProvider(Provider):
    """AvistaZ.to Provider."""
    subtitle_class = AvistazSubtitle
    languages = set(
        map(lambda lang: Language(lang.alpha_3),
            filter(None,
                   map(lookup_lang,
                       supported_languages_names))))
    languages.update(set(Language.rebuild(L, hi=True) for L in languages))

    video_types = (Episode, Movie)
    server_url = 'https://avistaz.to/'
    search_url = server_url + 'subtitles'

    def __init__(self, cookies=None):
        self.session = None
        self.cookies = cookies
        self.logged_in = False

    def initialize(self):
        self.session = RetryingCFSession()
        if self.cookies:
            from requests.cookies import RequestsCookieJar
            self.session.cookies = RequestsCookieJar()

            from http.cookies import SimpleCookie
            simple_cookie = SimpleCookie()
            simple_cookie.load(self.cookies)

            for k, v in simple_cookie.items():
                self.session.cookies.set(k, v.value)

            rr = self.session.get(self.server_url + 'rules', allow_redirects=False, timeout=10,
                                  headers={"Referer": self.server_url})
            if rr.status_code in [302, 404, 403]:
                logger.info('AvistaZ: Login expired')
                raise AuthenticationError("cookies not valid anymore")

            store_verification("avistaz", self.session)
            logger.debug('AvistaZ: Logged in')
            self.logged_in = True
            time.sleep(2)
            return True

    def terminate(self):
        self.session.close()

    def _query(self, video):
        subtitles = []

        req_type = 0
        titles = []
        if isinstance(video, Movie):
            req_type = 1
            titles = [video.title] + video.alternative_titles
        elif isinstance(video, Episode):
            req_type = 2
            titles = [video.series] + video.alternative_series

        for i, title in enumerate(titles):
            if i > 1:
                time.sleep(2)

            self._query_avistaz(subtitles, title, req_type, video)

        return subtitles

    def _query_avistaz(self, subtitles, title, req_type, video):
        logger.debug(f'AvistaZ: Querying {title}')

        r = self.session.get(self.search_url, params={
            'type': req_type,
            'search': title,
            'language': 0,
            'subtitle': 0,
            'uploader': ''
        }, timeout=30)
        r.raise_for_status()

        soup = ParserBeautifulSoup(r.content.decode('utf-8', 'ignore'), ['html.parser'])
        rows = soup.select('#content-area > div:nth-child(3) > div > table > tbody > tr')

        logger.debug(f'AvistaZ: Found {len(rows)}')

        for row_soup in rows:
            lang = lookup_lang(row_soup.select_one('td:nth-child(3) > a').text.strip())

            if lang is not None:
                download_link = row_soup.select_one('td:nth-of-type(4) > a')['href']
                srt_filename = download_link.split('/')[-1]

                release_td = row_soup.select_one('td:nth-child(2) > div:nth-child(1) > a')
                release = release_td.text

                guess = guessit(release)

                logger.debug(f'AvistaZ guess: {guess}')

                subtitle = self.subtitle_class(
                    page_link=release_td['href'],
                    download_link=download_link,
                    language=Language(lang.alpha_3),
                    video=video,
                    srt_filename=srt_filename,
                    release=release,
                    data=guess,
                    uploader=row_soup.select_one('td:nth-of-type(7) > span > a').text,
                )
                logger.debug(subtitle)
                subtitles.append(subtitle)

    def list_subtitles(self, video, languages):
        subtitles = []

        subtitles += [s for s in self._query(video) if s.language in languages]

        return subtitles

    def download_subtitle(self, subtitle):
        subtitle.content = self.session.get(subtitle.download_link).content
