# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import io
import os

from requests import Session
from guessit import guessit
from subliminal_patch.providers import Provider
from subliminal_patch.subtitle import Subtitle
from subliminal.utils import sanitize_release_group
from subliminal.subtitle import guess_matches
from subzero.language import Language

import gzip
import random
from time import sleep
from xml.etree import ElementTree

logger = logging.getLogger(__name__)


class BSPlayerSubtitle(Subtitle):
    """BSPlayer Subtitle."""
    provider_name = 'bsplayer'
    hash_verifiable = True

    def __init__(self, language, filename, subtype, video, link):
        super(BSPlayerSubtitle, self).__init__(language)
        self.language = language
        self.filename = filename
        self.page_link = link
        self.subtype = subtype
        self.video = video

    @property
    def id(self):
        return self.page_link

    @property
    def release_info(self):
        return self.filename

    def get_matches(self, video):
        matches = set()
        matches |= guess_matches(video, guessit(self.filename))
        matches.add('hash')

        return matches


class BSPlayerProvider(Provider):
    """BSPlayer Provider."""
    languages = {Language('por', 'BR')} | {Language(l) for l in [
        'ara', 'bul', 'ces', 'dan', 'deu', 'ell', 'eng', 'fin', 'fra', 'hun', 'ita', 'jpn', 'kor', 'nld', 'pol', 'por',
        'ron', 'rus', 'spa', 'swe', 'tur', 'ukr', 'zho'
    ]}
    SEARCH_THROTTLE = 8
    hash_verifiable = True

    # batantly based on kodi's bsplayer plugin
    # also took from BSPlayer-Subtitles-Downloader
    def __init__(self):
        self.initialize()

    def initialize(self):
        self.session = Session()
        self.search_url = self.get_sub_domain()
        self.token = None
        self.login()

    def terminate(self):
        self.session.close()
        self.logout()

    def api_request(self, func_name='logIn', params='', tries=5):
        headers = {
            'User-Agent': 'BSPlayer/2.x (1022.12360)',
            'Content-Type': 'text/xml; charset=utf-8',
            'Connection': 'close',
            'SOAPAction': '"http://api.bsplayer-subtitles.com/v1.php#{func_name}"'.format(func_name=func_name)
        }
        data = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ns1="{search_url}">'
            '<SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            '<ns1:{func_name}>{params}</ns1:{func_name}></SOAP-ENV:Body></SOAP-ENV:Envelope>'
        ).format(search_url=self.search_url, func_name=func_name, params=params)
        logger.info('Sending request: %s.' % func_name)
        for i in iter(range(tries)):
            try:
                self.session.headers.update(headers.items())
                res = self.session.post(self.search_url, data)
                return ElementTree.fromstring(res.text)

            except Exception as ex:
                logger.info("ERROR: %s." % ex)
                if func_name == 'logIn':
                    self.search_url = self.get_sub_domain()

                sleep(1)
        logger.info('ERROR: Too many tries (%d)...' % tries)
        raise Exception('Too many tries...')

    def login(self):
        # If already logged in
        if self.token:
            return True

        root = self.api_request(
            func_name='logIn',
            params=('<username></username>'
                    '<password></password>'
                    '<AppID>BSPlayer v2.67</AppID>')
        )
        res = root.find('.//return')
        if res.find('status').text == 'OK':
            self.token = res.find('data').text
            logger.info("Logged In Successfully.")
            return True
        return False

    def logout(self):
        # If already logged out / not logged in
        if not self.token:
            return True

        root = self.api_request(
            func_name='logOut',
            params='<handle>{token}</handle>'.format(token=self.token)
        )
        res = root.find('.//return')
        self.token = None
        if res.find('status').text == 'OK':
            logger.info("Logged Out Successfully.")
            return True
        return False

    def query(self, video, video_hash, language):
        if not self.login():
            return []

        if isinstance(language, (tuple, list, set)):
            # language_ids = ",".join(language)
            # language_ids = 'spa'
            language_ids = ','.join(sorted(l.opensubtitles for l in language))

        if video.imdb_id is None:
            imdbId = '*'
        else:
            imdbId = video.imdb_id
        sleep(self.SEARCH_THROTTLE)
        root = self.api_request(
            func_name='searchSubtitles',
            params=(
                '<handle>{token}</handle>'
                '<movieHash>{movie_hash}</movieHash>'
                '<movieSize>{movie_size}</movieSize>'
                '<languageId>{language_ids}</languageId>'
                '<imdbId>{imdbId}</imdbId>'
            ).format(token=self.token, movie_hash=video_hash,
                     movie_size=video.size, language_ids=language_ids, imdbId=imdbId)
        )
        res = root.find('.//return/result')
        if res.find('status').text != 'OK':
            return []

        items = root.findall('.//return/data/item')
        subtitles = []
        if items:
            logger.info("Subtitles Found.")
            for item in items:
                subID = item.find('subID').text
                subDownloadLink = item.find('subDownloadLink').text
                subLang = Language.fromopensubtitles(item.find('subLang').text)
                subName = item.find('subName').text
                subFormat = item.find('subFormat').text
                subtitles.append(
                    BSPlayerSubtitle(subLang, subName, subFormat, video, subDownloadLink)
                )
        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, video.hashes['bsplayer'], languages)

    def get_sub_domain(self):
        # s1-9, s101-109
        SUB_DOMAINS = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9',
                       's101', 's102', 's103', 's104', 's105', 's106', 's107', 's108', 's109']
        API_URL_TEMPLATE = "http://{sub_domain}.api.bsplayer-subtitles.com/v1.php"
        sub_domains_end = len(SUB_DOMAINS) - 1
        return API_URL_TEMPLATE.format(sub_domain=SUB_DOMAINS[random.randint(0, sub_domains_end)])

    def download_subtitle(self, subtitle):
        session = Session()
        _addheaders = {
            'User-Agent': 'Mozilla/4.0 (compatible; Synapse)'
        }
        session.headers.update(_addheaders)
        res = session.get(subtitle.page_link)
        if res:
            if res.text == '500':
                raise ValueError('Error 500 on server')

            with gzip.GzipFile(fileobj=io.BytesIO(res.content)) as gf:
                subtitle.content = gf.read()
                subtitle.normalize()

            return subtitle
        raise ValueError('Problems conecting to the server')
