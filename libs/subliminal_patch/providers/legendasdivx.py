# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import io
import os
import sys
import rarfile
import zipfile

from requests import Session
from guessit import guessit
from subliminal_patch.exceptions import ParseResponseError
from subliminal_patch.providers import Provider
from subliminal.providers import ParserBeautifulSoup
from subliminal_patch.subtitle import Subtitle
from subliminal_patch.utils import sanitize
from subliminal.exceptions import ProviderError
from subliminal.utils import sanitize_release_group
from subliminal.subtitle import guess_matches
from subliminal.video import Episode, Movie
from subliminal.subtitle import SUBTITLE_EXTENSIONS, fix_line_ending,guess_matches
from subzero.language import Language

import gzip

logger = logging.getLogger(__name__)

class LegendasdivxSubtitle(Subtitle):
    """Legendasdivx Subtitle."""
    provider_name = 'legendasdivx'

    def __init__(self, language, video, data):
        super(LegendasdivxSubtitle, self).__init__(language)
        self.language = language
        self.page_link = data['link']
        self.hits=data['hits']
        self.exact_match=data['exact_match']
        self.description=data['description'].lower()
        self.video = video
        self.videoname =data['videoname']

    @property
    def id(self):
        return self.page_link

    @property
    def release_info(self):
        return self.description

    def get_matches(self, video):
        matches = set()

        if self.videoname.lower() in self.description:
            matches.update(['title'])
            matches.update(['season'])
            matches.update(['episode'])

        # episode
        if video.title and video.title.lower() in self.description:
            matches.update(['title'])
        if video.year and '{:04d}'.format(video.year) in self.description:
            matches.update(['year'])

        if isinstance(video, Episode):
            # already matched in search query
            if video.season and 's{:02d}'.format(video.season) in self.description:
                matches.update(['season'])
            if video.episode and 'e{:02d}'.format(video.episode) in self.description:
                matches.update(['episode'])
            if video.episode and video.season and video.series:
                if '{}.s{:02d}e{:02d}'.format(video.series.lower(),video.season,video.episode) in self.description:
                        matches.update(['series'])
                        matches.update(['season'])
                        matches.update(['episode'])
                if '{} s{:02d}e{:02d}'.format(video.series.lower(),video.season,video.episode) in self.description:
                    matches.update(['series'])
                    matches.update(['season'])
                    matches.update(['episode'])

        # release_group
        if video.release_group  and video.release_group.lower() in self.description:
            matches.update(['release_group'])

        # resolution

        if video.resolution and video.resolution.lower() in self.description:
            matches.update(['resolution'])

        # format
        formats = []
        if video.format:
            formats = [video.format.lower()]
            if formats[0] == "web-dl":
                formats.append("webdl")
                formats.append("webrip")
                formats.append("web ")
            for frmt in formats:
                if frmt.lower() in self.description:
                    matches.update(['format'])
                    break

        # video_codec
        if video.video_codec:
            video_codecs = [video.video_codec.lower()]
            if video_codecs[0] == "h264":
                formats.append("x264")
            elif video_codecs[0] == "h265":
                formats.append("x265")
            for vc in formats:
                if vc.lower() in self.description:
                    matches.update(['video_codec'])
                    break

        matches |= guess_matches(video, guessit(self.description))
        return matches




class LegendasdivxProvider(Provider):
    """Legendasdivx Provider."""
    languages = {Language('por', 'BR')} | {Language('por')}
    SEARCH_THROTTLE = 8
    site = 'https://www.legendasdivx.pt'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Origin': 'https://www.legendasdivx.pt',
        'Referer': 'https://www.legendasdivx.pt',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    loginpage = site + '/forum/ucp.php?mode=login'
    searchurl = site + '/modules.php?name=Downloads&file=jz&d_op=search&op=_jz00&query={query}'
    language_list = list(languages)


    def __init__(self, username, password):
        self.username = username
        self.password = password

    def initialize(self):
        self.session = Session()
        self.login()

    def terminate(self):
        self.logout()
        self.session.close()

    def login(self):
        logger.info('Logging in')
        self.headers['Referer'] = self.site + '/index.php'
        self.session.headers.update(self.headers.items())
        res = self.session.get(self.loginpage)
        bsoup = ParserBeautifulSoup(res.content, ['lxml'])

        _allinputs = bsoup.findAll('input')
        fields = {}
        for field in _allinputs:
            fields[field.get('name')] = field.get('value')

        fields['username'] = self.username
        fields['password'] = self.password
        fields['autologin'] = 'on'
        fields['viewonline'] = 'on'

        self.headers['Referer'] = self.loginpage
        self.session.headers.update(self.headers.items())
        res = self.session.post(self.loginpage, fields)
        try:
            logger.debug('Got session id %s' %
                         self.session.cookies.get_dict()['PHPSESSID'])
        except KeyError as e:
            logger.error(repr(e))
            logger.error("Didn't get session id, check your credentials")
            return False
        except Exception as e:
            logger.error(repr(e))
            logger.error('uncached error #legendasdivx #AA')
            return False

        return True
    def logout(self):
        # need to figure this out
        return True

    def query(self, video, language):
        try:
            logger.debug('Got session id %s' %
                         self.session.cookies.get_dict()['PHPSESSID'])
        except Exception as e:
            self.login()
            return []

        language_ids = '0'
        if isinstance(language, (tuple, list, set)):
            if len(language) == 1:
                language_ids = ','.join(sorted(l.opensubtitles for l in language))
                if language_ids == 'por':
                    language_ids = '&form_cat=28'
                else:
                    language_ids = '&form_cat=29'

        querytext = video.name
        querytext = os.path.basename(querytext)
        querytext, _ = os.path.splitext(querytext)
        videoname = querytext
        querytext = querytext.lower()
        querytext = querytext.replace(
            ".", "+").replace("[", "").replace("]", "")
        if language_ids != '0':
            querytext = querytext + language_ids
        self.headers['Referer'] = self.site + '/index.php'
        self.session.headers.update(self.headers.items())
        res = self.session.get(self.searchurl.format(query=querytext))
        # form_cat=28 = br
        # form_cat=29 = pt
        if "A legenda não foi encontrada" in res.text:
            logger.warning('%s not found', querytext)
            return []

        bsoup = ParserBeautifulSoup(res.content, ['html.parser'])
        _allsubs = bsoup.findAll("div", {"class": "sub_box"})
        subtitles = []
        lang = Language.fromopensubtitles("pob")
        for _subbox in _allsubs:
            hits=0
            for th in _subbox.findAll("th", {"class": "color2"}):
                if th.string == 'Hits:':
                    hits = int(th.parent.find("td").string)
                if th.string == 'Idioma:':
                    lang = th.parent.find("td").find ("img").get ('src')
                    if 'brazil' in lang:
                        lang = Language.fromopensubtitles('pob')
                    else:
                        lang = Language.fromopensubtitles('por')


            description = _subbox.find("td", {"class": "td_desc brd_up"})
            download = _subbox.find("a", {"class": "sub_download"})
            try:
                # sometimes BSoup just doesn't get the link
                logger.debug(download.get('href'))
            except Exception as e:
                logger.warning('skipping subbox on %s' % self.searchurl.format(query=querytext))
                continue

            exact_match = False
            if video.name.lower() in description.get_text().lower():
                exact_match = True
            data = {'link': self.site + '/modules.php' + download.get('href'),
                    'exact_match': exact_match,
                    'hits': hits,
                    'videoname': videoname,
                    'description': description.get_text() }
            subtitles.append(
                LegendasdivxSubtitle(lang, video, data)
            )

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(video, languages)

    def download_subtitle(self, subtitle):
        res = self.session.get(subtitle.page_link)
        if res:
            if res.text == '500':
                raise ValueError('Error 500 on server')

            archive = self._get_archive(res.content)
            # extract the subtitle
            subtitle_content = self._get_subtitle_from_archive(archive)
            subtitle.content = fix_line_ending(subtitle_content)
            subtitle.normalize()

            return subtitle
        raise ValueError('Problems conecting to the server')

    def _get_archive(self, content):
        # open the archive
        # stole^H^H^H^H^H inspired from subvix provider
        archive_stream = io.BytesIO(content)
        if rarfile.is_rarfile(archive_stream):
            logger.debug('Identified rar archive')
            archive = rarfile.RarFile(archive_stream)
        elif zipfile.is_zipfile(archive_stream):
            logger.debug('Identified zip archive')
            archive = zipfile.ZipFile(archive_stream)
        else:
            # raise ParseResponseError('Unsupported compressed format')
            raise Exception('Unsupported compressed format')

        return archive

    def _get_subtitle_from_archive(self, archive):
        for name in archive.namelist():
            # discard hidden files
            if os.path.split(name)[-1].startswith('.'):
                continue

            # discard non-subtitle files
            if not name.lower().endswith(SUBTITLE_EXTENSIONS):
                continue

            return archive.read(name)

        raise ParseResponseError('Can not find the subtitle in the compressed file')
