# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import time
from http.cookies import SimpleCookie
from random import randint

import pycountry
from requests.cookies import RequestsCookieJar
from subliminal.exceptions import AuthenticationError
from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.http import RetryingCFSession
from subliminal_patch.pitcher import store_verification
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subzero.language import Language
from .utils import get_archive_from_bytes, get_subtitle_from_archive, FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

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
        return Language(pycountry.languages.lookup(name).alpha_3)
    except:
        return None


class AvistazSubtitle(Subtitle):
    """AvistaZ.to Subtitle."""
    provider_name = 'avistaz'

    def __init__(self, page_link, download_link, language, video, filename, release, uploader):
        super().__init__(language, page_link=page_link)
        self.hearing_impaired = None
        self.language = language
        self.filename = filename
        self.release_info = release
        self.page_link = page_link
        self.download_link = download_link
        self.video = video
        self.matches = None
        self.content = None
        self.uploader = uploader
        self.encoding = None

    @property
    def id(self):
        return self.filename

    def get_matches(self, video):
        # we download subtitles directly from the
        # release page, so it's always a perfect match
        self.matches = {'hash'}
        return self.matches


class AvistazProvider(Provider):
    """AvistaZ.to Provider."""
    subtitle_class = AvistazSubtitle
    languages = set(filter(None, map(lookup_lang, supported_languages_names)))
    languages.update(set(Language.rebuild(L, hi=True) for L in languages))

    server_url = 'https://avistaz.to/'
    hash_verifiable = True

    def __init__(self, cookies, user_agent=None):
        self.session = None
        self.cookies = cookies
        self.user_agent = user_agent

    def initialize(self):
        self.session = RetryingCFSession()

        if self.user_agent:
            self.session.headers['User-Agent'] = self.user_agent
        else:
            self.session.headers['User-Agent'] = AGENT_LIST[randint(0, len(AGENT_LIST) - 1)]

        if self.cookies:
            self.session.cookies = RequestsCookieJar()
            simple_cookie = SimpleCookie()
            simple_cookie.load(self.cookies)

            for k, v in simple_cookie.items():
                self.session.cookies.set(k, v.value)

            rr = self.session.get(self.server_url + 'rules', allow_redirects=False, timeout=10,
                                  headers={"Referer": self.server_url})
            if rr.status_code in [302, 404, 403]:
                logger.info('Cookies expired')
                raise AuthenticationError("cookies not valid anymore")

            store_verification("avistaz", self.session)
            logger.debug('Cookies valid')
            time.sleep(2)
            return True

    def terminate(self):
        self.session.close()

    def list_subtitles(self, video, languages):
        if video.info_url is None or 'avistaz.to' not in video.info_url:
            logger.debug('%s not downloaded from AvistaZ. Skipped', video)
            return []

        release = self._parse_release_table(self._query_info_url(video.info_url))

        if release['Subtitles'].table is None:
            logger.debug('No subtitles found for %s', video)
            return []

        subtitle_columns = list(map(lambda x: x.get_text(), release['Subtitles'].thead.find_all('th')))

        subtitles = []
        for row in release['Subtitles'].tbody.find_all('tr', recursive=False):

            subtitle_cols = self._parse_subtitle_row(row, subtitle_columns)

            release_name = release['Title'].get_text().strip()
            lang = lookup_lang(subtitle_cols['Language'].get_text().strip())
            download_link = subtitle_cols['Download'].a['href']
            uploader_name = subtitle_cols['Uploader'].get_text().strip()

            if lang not in languages:
                continue

            subtitles.append(self.subtitle_class(
                page_link=video.info_url,
                download_link=download_link,
                language=lang,
                video=video,
                filename=download_link.split('/')[-1],
                release=release_name,
                uploader=uploader_name,
            ))

        return subtitles

    def _query_info_url(self, info_url):
        response = self.session.get(info_url, timeout=30)
        response.raise_for_status()

        return response.content.decode('utf-8', 'ignore')

    def _parse_subtitle_row(self, row, subtitle_columns):
        columns = {}
        for i, data in enumerate(row.find_all('td', recursive=False)):
            columns[subtitle_columns[i]] = data
        return columns

    def _parse_release_table(self, html):
        release_data_table = (ParserBeautifulSoup(html, ['html.parser'])
                              .select_one('#content-area > div:nth-child(4) > div.table-responsive > table > tbody'))

        rows = {}
        for tr in release_data_table.find_all('tr', recursive=False):
            rows[tr.td.get_text()] = tr.select_one('td:nth-child(2)', recursive=False)
        return rows

    def download_subtitle(self, subtitle):
        response = self.session.get(subtitle.download_link)
        response.raise_for_status()
        if subtitle.filename.endswith((".zip", ".rar")):
            archive = get_archive_from_bytes(response.content)
            subtitle.content = get_subtitle_from_archive(
                archive, episode=subtitle.video.episode
            )
        else:
            subtitle.content = response.content
