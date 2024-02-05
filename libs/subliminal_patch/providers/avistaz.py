# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import time

import pycountry
from guessit import guessit
from ratelimiter import RateLimiter
from subliminal.exceptions import AuthenticationError
from subliminal.providers import ParserBeautifulSoup
from subliminal.video import Episode, Movie
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.pitcher import store_verification
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle, guess_matches
from subzero.language import Language
from .utils import get_archive_from_bytes, get_subtitle_from_archive

logger = logging.getLogger(__name__)

# extracted from Su
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


def _log_rate_limited(until):
    logger.info('Rate limited, sleeping for %s seconds', int(round(until - time.time())))


@RateLimiter(max_calls=1, period=1, callback=_log_rate_limited)
def _rate_limited(method):
    return method()


class AvistazSubtitle(Subtitle):
    """AvistaZ.to Subtitle."""
    provider_name = 'avistaz'

    def __init__(self, page_link, download_link, language, video, filename, release, guess, uploader):
        super().__init__(language, page_link=page_link)
        self.language = language
        self.filename = filename
        self.srt_filename = filename
        self.release_info = release
        self.page_link = page_link
        self.download_link = download_link
        self.data = guess
        self.video = video
        self.matches = None
        self.content = None
        self.hearing_impaired = None
        self.uploader = uploader
        self.encoding = None
        self.is_pack = 'episode' not in guess and 'other' in guess and 'complete' in guess['other'].lower()

    @property
    def id(self):
        return self.srt_filename

    def get_matches(self, video):
        # guess additional info from data
        matches = guess_matches(video, self.data)

        # if the release group matches, the source is most likely correct, as well
        if "release_group" in matches:
            matches.add("source")

        if isinstance(video, Episode):
            if (video.original_series and 'year' not in self.data) or (
                    video.year and 'year' in self.data and self.data['year'] == video.year):
                matches.add('year')

            if ('season' not in self.data or 'season' in matches) and self.is_pack:
                matches.add('episode')
                matches.add('season')

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

            rr = _rate_limited(lambda: self.session.get(self.server_url + 'rules', allow_redirects=False, timeout=10,
                                                        headers={"Referer": self.server_url}))
            if rr.status_code in [302, 404, 403]:
                logger.info('Login expired')
                raise AuthenticationError("cookies not valid anymore")

            store_verification("avistaz", self.session)
            logger.debug('Logged in')
            self.logged_in = True
            time.sleep(2)
            return True

    def terminate(self):
        self.session.close()

    def _list_subtitles(self, video):
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
            html = self._query_subtitles(title, req_type)
            rows = self._find_subtitle_rows(html)

            logger.debug('Found %s subtitles', len(rows))
            for row_soup in rows:
                download_link, file_name, lang_name, release_link, release_name, uploader_name = self._parse_row(
                    row_soup)

                lang = lookup_lang(lang_name)
                if lang is None:
                    continue

                subtitle = self.subtitle_class(
                    page_link=release_link,
                    download_link=download_link,
                    language=Language(lang.alpha_3),
                    video=video,
                    filename=file_name,
                    release=release_name,
                    guess=guessit(release_name),
                    uploader=uploader_name,
                )

                subtitles.append(subtitle)

        return subtitles

    def _query_subtitles(self, title, req_type):
        response = _rate_limited(lambda: self.session.get(self.search_url, params={
            'type': req_type,
            'search': title,
            'language': 0,
            'subtitle': 0,
            'uploader': ''
        }, timeout=30))
        response.raise_for_status()

        return response.content.decode('utf-8', 'ignore')

    def _find_subtitle_rows(self, html):
        soup = ParserBeautifulSoup(html, ['html.parser'])
        rows = soup.select('#content-area > div:nth-child(3) > div > table > tbody > tr')
        return rows

    def _parse_row(self, row_soup):
        lang_name = row_soup.select_one('td:nth-child(3) > a').text.strip()
        download_link = row_soup.select_one('td:nth-of-type(4) > a')['href']
        file_name = download_link.split('/')[-1]
        release_td = row_soup.select_one('td:nth-child(2) > div:nth-child(1) > a')
        release_name = release_td.text.strip()
        release_link = release_td['href']
        uploader_name = row_soup.select_one('td:nth-of-type(7) > span > a').text.strip()

        return download_link, file_name, lang_name, release_link, release_name, uploader_name

    def list_subtitles(self, video, languages):
        subtitles = []

        subtitles += [s for s in self._list_subtitles(video) if s.language in languages]

        return subtitles

    def download_subtitle(self, subtitle):
        response = _rate_limited(lambda: self.session.get(subtitle.download_link))
        response.raise_for_status()
        if subtitle.filename.endswith((".zip", ".rar")):
            archive = get_archive_from_bytes(response.content)
            subtitle.content = get_subtitle_from_archive(
                archive, episode=subtitle.video.episode
            )
        else:
            subtitle.content = response.content
