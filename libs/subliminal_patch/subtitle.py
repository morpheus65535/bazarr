# coding=utf-8


import logging
import traceback

import re
import types

import chardet
import pysrt
import pysubs2
from bs4 import UnicodeDammit
from pysubs2 import SSAStyle
from pysubs2.subrip import parse_tags, MAX_REPRESENTABLE_TIME
from pysubs2.time import ms_to_times
from subzero.modification import SubtitleModifications
from subliminal import Subtitle as Subtitle_
from subliminal.subtitle import Episode, Movie, sanitize_release_group, get_equivalent_release_groups
from subliminal_patch.utils import sanitize
from ftfy import fix_text

logger = logging.getLogger(__name__)


ftfy_defaults = {
    "uncurl_quotes": False,
    "fix_character_width": False,
}


class Subtitle(Subtitle_):
    storage_path = None
    release_info = None
    matches = None
    hash_verifiable = False
    hearing_impaired_verifiable = False
    mods = None
    plex_media_fps = None
    skip_wrong_fps = False
    wrong_fps = False
    wrong_series = False
    wrong_season_ep = False
    is_pack = False
    asked_for_release_group = None
    asked_for_episode = None

    pack_data = None
    _guessed_encoding = None
    _is_valid = False

    def __init__(self, language, hearing_impaired=False, page_link=None, encoding=None, mods=None):
        super(Subtitle, self).__init__(language, hearing_impaired=hearing_impaired, page_link=page_link,
                                       encoding=encoding)
        self.mods = mods
        self._is_valid = False

    def __repr__(self):
        return '<%s %r [%s:%s]>' % (
            self.__class__.__name__, self.page_link, self.language, self._guessed_encoding)

    @property
    def text(self):
        """Content as string

        If :attr:`encoding` is None, the encoding is guessed with :meth:`guess_encoding`

        """
        if not self.content:
            return

        #if self.encoding:
        #    return fix_text(self.content.decode(self.encoding, errors='replace'), **ftfy_defaults)

        return self.content.decode(self.guess_encoding(), errors='replace')

    @property
    def numeric_id(self):
        raise NotImplemented

    def make_picklable(self):
        """
        some subtitle instances might have unpicklable objects stored; clean them up here 
        :return: self
        """
        return self

    def set_encoding(self, encoding):
        ge = self.guess_encoding()
        if encoding == ge:
            return

        unicontent = self.text
        logger.debug("Changing encoding: to %s, from %s", encoding, ge)
        self.content = unicontent.encode(encoding)
        self._guessed_encoding = encoding

    def normalize(self):
        """
        Set encoding to UTF-8 and normalize line endings
        :return:
        """
        self.set_encoding("utf-8")

        # normalize line endings
        self.content = self.content.replace("\r\n", "\n").replace('\r', '\n')

    def guess_encoding(self):
        """Guess encoding using the language, falling back on chardet.

        :return: the guessed encoding.
        :rtype: str

        """
        if self._guessed_encoding:
            return self._guessed_encoding

        logger.info('Guessing encoding for language %s', self.language)

        encodings = ['utf-8']

        # add language-specific encodings
        # http://scratchpad.wikia.com/wiki/Character_Encoding_Recommendation_for_Languages

        if self.language.alpha3 == 'zho':
            encodings.extend(['cp936', 'gb2312', 'gbk', 'gb18030', 'hz', 'iso2022_jp_2', 'cp950', 'gb18030', 'big5',
                              'big5hkscs', 'utf-16'])
        elif self.language.alpha3 == 'jpn':
            encodings.extend(['shift-jis', 'cp932', 'euc_jp', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2',
                              'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', ])
        elif self.language.alpha3 == 'tha':
            encodings.extend(['tis-620', 'cp874'])

        # arabian/farsi
        elif self.language.alpha3 in ('ara', 'fas', 'per'):
            encodings.extend(['windows-1256', 'utf-16'])
        elif self.language.alpha3 == 'heb':
            encodings.extend(['windows-1255', 'iso-8859-8'])
        elif self.language.alpha3 == 'tur':
            encodings.extend(['windows-1254', 'iso-8859-9', 'iso-8859-3'])

        # Greek
        elif self.language.alpha3 in ('grc', 'gre', 'ell'):
            encodings.extend(['windows-1253', 'cp1253', 'cp737', 'iso8859-7', 'cp875', 'cp869', 'iso2022_jp_2',
                              'mac_greek'])

        # Polish, Czech, Slovak, Hungarian, Slovene, Bosnian, Croatian, Serbian (Latin script),
        # Romanian and Albanian
        elif self.language.alpha3 in ('pol', 'cze', 'ces', 'slk', 'slo', 'slv', 'hun', 'bos', 'hbs', 'hrv', 'rsb',
                                      'ron', 'rum', 'sqi', 'alb'):

            encodings.extend(['windows-1250', 'iso-8859-2'])

            # Eastern European Group 1
            if self.language.alpha3 == "slv":
                encodings.append('iso-8859-4')

            # Albanian
            elif self.language.alpha3 in ("sqi", "alb"):
                encodings.extend(['windows-1252', 'iso-8859-15', 'iso-8859-1', 'iso-8859-9'])

        # Bulgarian, Serbian and Macedonian, Ukranian and Russian
        elif self.language.alpha3 in ('bul', 'srp', 'mkd', 'mac', 'rus', 'ukr'):
            # Eastern European Group 2
            if self.language.alpha3 in ('bul', 'mkd', 'mac', 'rus', 'ukr'):
                encodings.extend(['windows-1251', 'iso-8859-5'])

            elif self.language.alpha3 == 'srp':
                if self.language.script == "Latn":
                    encodings.extend(['windows-1250', 'iso-8859-2'])
                elif self.language.script == "Cyrl":
                    encodings.extend(['windows-1251', 'iso-8859-5'])
                else:
                    encodings.extend(['windows-1250', 'windows-1251', 'iso-8859-2', 'iso-8859-5'])

        else:
            # Western European (windows-1252) / Northern European
            encodings.extend(['latin-1', 'iso-8859-15', 'iso-8859-9', 'iso-8859-4', 'iso-8859-1'])

        # try to decode
        logger.debug('Trying encodings %r', encodings)
        for encoding in encodings:
            try:
                self.content.decode(encoding)

            except UnicodeDecodeError:
                pass
            else:
                logger.info('Guessed encoding %s', encoding)
                self._guessed_encoding = encoding
                return encoding

        logger.warning('Could not guess encoding from language')

        # fallback on chardet
        encoding = chardet.detect(self.content)['encoding']
        logger.info('Chardet found encoding %s', encoding)

        if not encoding:
            # fallback on bs4
            logger.info('Falling back to bs4 detection')
            a = UnicodeDammit(self.content)

            logger.info("bs4 detected encoding: %s", a.original_encoding)

            if a.original_encoding:
                self._guessed_encoding = a.original_encoding
                return a.original_encoding
            raise ValueError(u"Couldn't guess the proper encoding for %s", self)

        self._guessed_encoding = encoding
        return encoding

    def is_valid(self):
        """Check if a :attr:`text` is a valid SubRip format.

        :return: whether or not the subtitle is valid.
        :rtype: bool

        """
        if self._is_valid:
            return True

        text = self.text
        if not text:
            return False

        # valid srt
        try:
            pysrt.from_string(text, error_handling=pysrt.ERROR_RAISE)
        except Exception:
            logger.error("PySRT-parsing failed, trying pysubs2")
        else:
            self._is_valid = True
            return True

        # something else, try to return srt
        try:
            logger.debug("Trying parsing with PySubs2")
            try:
                # in case of microdvd, try parsing the fps from the subtitle
                subs = pysubs2.SSAFile.from_string(text)
                if subs.format == "microdvd":
                    logger.info("Got FPS from MicroDVD subtitle: %s", subs.fps)
                else:
                    logger.info("Got format: %s", subs.format)
            except pysubs2.UnknownFPSError:
                # if parsing failed, suggest our media file's fps
                logger.info("No FPS info in subtitle. Using our own media FPS for the MicroDVD subtitle: %s",
                            self.plex_media_fps)
                subs = pysubs2.SSAFile.from_string(text, fps=self.plex_media_fps)

            unicontent = self.pysubs2_to_unicode(subs)
            self.content = unicontent.encode(self._guessed_encoding)
        except:
            logger.exception("Couldn't convert subtitle %s to .srt format: %s", self, traceback.format_exc())
            return False

        self._is_valid = True
        return True

    @classmethod
    def pysubs2_to_unicode(cls, sub, format="srt"):
        def ms_to_timestamp(ms, mssep=","):
            """Convert ms to 'HH:MM:SS,mmm'"""
            # XXX throw on overflow/underflow?
            if ms < 0: ms = 0
            if ms > MAX_REPRESENTABLE_TIME: ms = MAX_REPRESENTABLE_TIME
            h, m, s, ms = ms_to_times(ms)
            return "%02d:%02d:%02d%s%03d" % (h, m, s, mssep, ms)

        def prepare_text(text, style):
            body = []
            for fragment, sty in parse_tags(text, style, sub.styles):
                fragment = fragment.replace(ur"\h", u" ")
                fragment = fragment.replace(ur"\n", u"\n")
                fragment = fragment.replace(ur"\N", u"\n")
                if format == "srt":
                    if sty.italic:
                        fragment = u"<i>%s</i>" % fragment
                    if sty.underline:
                        fragment = u"<u>%s</u>" % fragment
                    if sty.strikeout:
                        fragment = u"<s>%s</s>" % fragment
                elif format == "vtt":
                    if sty.bold:
                        fragment = u"<b>%s</b>" % fragment
                    if sty.italic:
                        fragment = u"<i>%s</i>" % fragment
                    if sty.underline:
                        fragment = u"<u>%s</u>" % fragment

                body.append(fragment)

            return re.sub(u"\n+", u"\n", u"".join(body).strip())

        visible_lines = (line for line in sub if not line.is_comment)

        out = []
        mssep = ","

        if format == "vtt":
            out.append("WEBVTT\n\n")
            mssep = "."

        for i, line in enumerate(visible_lines, 1):
            start = ms_to_timestamp(line.start, mssep=mssep)
            end = ms_to_timestamp(line.end, mssep=mssep)
            text = prepare_text(line.text, sub.styles.get(line.style, SSAStyle.DEFAULT_STYLE))

            out.append(u"%d\n" % i)
            out.append(u"%s --> %s\n" % (start, end))
            out.append(u"%s%s" % (text, "\n\n"))

        return u"".join(out)

    def get_modified_content(self, format="srt", debug=False):
        """
        :return: string 
        """
        if not self.mods:
            return fix_text(self.content.decode(encoding=self._guessed_encoding), **ftfy_defaults).encode(
                encoding=self._guessed_encoding)

        submods = SubtitleModifications(debug=debug)
        if submods.load(content=self.text, language=self.language):
            logger.info("Applying mods: %s", self.mods)
            submods.modify(*self.mods)
            self.mods = submods.mods_used

            content = fix_text(self.pysubs2_to_unicode(submods.f, format=format), **ftfy_defaults)\
                .encode(encoding=self._guessed_encoding)
            submods.f = None
            del submods
            return content
        return None


class ModifiedSubtitle(Subtitle):
    id = None


def guess_matches(video, guess, partial=False):
    """Get matches between a `video` and a `guess`.

    If a guess is `partial`, the absence information won't be counted as a match.

    Patch: add multiple release group and formats handling

    :param video: the video.
    :type video: :class:`~subliminal.video.Video`
    :param guess: the guess.
    :type guess: dict
    :param bool partial: whether or not the guess is partial.
    :return: matches between the `video` and the `guess`.
    :rtype: set

    """

    matches = set()
    if isinstance(video, Episode):
        # series
        if video.series and 'title' in guess:
            titles = guess["title"]
            if not isinstance(titles, types.ListType):
                titles = [titles]

            for title in titles:
                if sanitize(title) in (sanitize(name) for name in [video.series] + video.alternative_series):
                    matches.add('series')
        # title
        if video.title and 'episode_title' in guess and sanitize(guess['episode_title']) == sanitize(video.title):
            matches.add('title')
        # season
        if video.season and 'season' in guess and guess['season'] == video.season:
            matches.add('season')
        # episode
        # Currently we only have single-ep support (guessit returns a multi-ep as a list with int values)
        # Most providers only support single-ep, so make sure it contains only 1 episode
        # In case of multi-ep, take the lowest episode (subtitles will normally be available on lowest episode number)
        if video.episode and 'episode' in guess:
            episode_guess = guess['episode']
            episode = min(episode_guess) if episode_guess and isinstance(episode_guess, list) else episode_guess
            if episode == video.episode:
                matches.add('episode')
        # year
        if video.year and 'year' in guess and guess['year'] == video.year:
            matches.add('year')
        # count "no year" as an information
        if not partial and video.original_series and 'year' not in guess:
            matches.add('year')
    elif isinstance(video, Movie):
        # year
        if video.year and 'year' in guess and guess['year'] == video.year:
            matches.add('year')
        # title
        if video.title and 'title' in guess and sanitize(guess['title']) in (
                    sanitize(name) for name in [video.title] + video.alternative_titles):
            matches.add('title')

    # release_group
    if 'release_group' in guess:
        release_groups = guess["release_group"]
        if not isinstance(release_groups, types.ListType):
            release_groups = [release_groups]

        if video.release_group:
            for release_group in release_groups:
                if (sanitize_release_group(release_group) in
                        get_equivalent_release_groups(sanitize_release_group(video.release_group))):
                    matches.add('release_group')
                    break

    # resolution
    if video.resolution and 'screen_size' in guess and guess['screen_size'] == video.resolution:
        matches.add('resolution')

    # format
    if 'format' in guess:
        formats = guess["format"]
        if not isinstance(formats, types.ListType):
            formats = [formats]

        if video.format:
            video_format = video.format
            if video_format in ("HDTV", "SDTV", "TV"):
                video_format = "TV"
                logger.debug("Treating HDTV/SDTV the same")

            for frmt in formats:
                if frmt in ("HDTV", "SDTV"):
                    frmt = "TV"

                if frmt.lower() == video_format.lower():
                    matches.add('format')
                    break
    # video_codec
    if video.video_codec and 'video_codec' in guess and guess['video_codec'] == video.video_codec:
        matches.add('video_codec')
    # audio_codec
    if video.audio_codec and 'audio_codec' in guess and guess['audio_codec'] == video.audio_codec:
        matches.add('audio_codec')

    return matches
