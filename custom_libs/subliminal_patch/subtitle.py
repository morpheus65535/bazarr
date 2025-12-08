# coding=utf-8


from __future__ import absolute_import
import logging
import traceback

import re
import types

import chardet
import pysrt
import pysubs2
from bs4 import UnicodeDammit
from copy import deepcopy
from subzero.modification import SubtitleModifications
from subzero.language import Language
from subliminal import Subtitle as Subtitle_
from subliminal.subtitle import Episode, Movie, sanitize_release_group, get_equivalent_release_groups
from subliminal_patch.utils import sanitize
from ftfy import fix_text
from codecs import BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE
from six import text_type

BOMS = (
    (BOM_UTF8, "UTF-8"),
    (BOM_UTF32_BE, "UTF-32-BE"),
    (BOM_UTF32_LE, "UTF-32-LE"),
    (BOM_UTF16_BE, "UTF-16-BE"),
    (BOM_UTF16_LE, "UTF-16-LE"),
)

logger = logging.getLogger(__name__)


ftfy_defaults = {
    "uncurl_quotes": False,
    "fix_character_width": False,
}


class Subtitle(Subtitle_):
    storage_path = None
    release_info = None
    matches = {}
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
    uploader = None # string - uploader username

    pack_data = None
    _guessed_encoding = None
    _is_valid = False
    use_original_format = False
    # format = "srt" # default format is srt

    def __init__(self, language, hearing_impaired=False, page_link=None, encoding=None, mods=None, original_format=False):
        # language needs to be cloned because it is actually a reference to the provider language object
        # if a new copy is not created then all subsequent subtitles for this provider will incorrectly be modified
        # at least until Bazarr is restarted or the provider language object is recreated somehow
        language = deepcopy(language)

        # set subtitle language to hi if it's hearing_impaired
        if hearing_impaired:
            language = Language.rebuild(language, hi=True)

        super(Subtitle, self).__init__(language, hearing_impaired=hearing_impaired, page_link=page_link,
                                       encoding=encoding)
        self.mods = mods
        self._is_valid = False
        self.use_original_format = original_format
        self._og_format = None

    @property
    def format(self):
        if self.use_original_format and self._og_format is not None:
            logger.debug("Original format requested [%s]", self._og_format)
            return self._og_format

        logger.debug("Will assume srt format")
        return "srt"

    # Compatibility
    @format.setter
    def format(self, val):
        self._og_format = val

    def __repr__(self):
        r_info = str(self.release_info or "").replace("\n", " | ").strip()
        return f"<{self.__class__.__name__}: {r_info} [{repr(self.language)}]>"

    @property
    def text(self):
        """Content as string

        If :attr:`encoding` is None, the encoding is guessed with :meth:`guess_encoding`

        """
        if not self.content:
            return

        if not isinstance(self.content, text_type):
            return self.content.decode(self.get_encoding(), errors='replace')

        return self.content

    @property
    def numeric_id(self):
        raise NotImplemented

    def get_fps(self):
        """
        :return: frames per second or None if not supported
        :rtype: float
        """
        return None

    def make_picklable(self):
        """
        some subtitle instances might have unpicklable objects stored; clean them up here
        :return: self
        """
        return self

    def get_encoding(self):
        return self.guess_encoding()

    def set_encoding(self, encoding):
        ge = self.get_encoding()
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
        if self.format == "srt":
            self.content = self.content.replace(b"\r\n", b"\n").replace(b'\r', b'\n')

    @staticmethod
    def _check_bom(data):
        return [encoding for bom, encoding in BOMS if data.startswith(bom)]

    def guess_encoding(self):
        """Guess encoding using the language, falling back on chardet.

        :return: the guessed encoding.
        :rtype: str

        """
        if self._guessed_encoding:
            return self._guessed_encoding

        if self.encoding:
            # check provider encoding and use it only if it is valid
            try:
                self.content.decode(self.encoding)
                self._guessed_encoding = self.encoding
                return self._guessed_encoding
            except:
                # provider specified encoding is invalid, fallback to guessing
                pass

        logger.info('Guessing encoding for language %s', self.language)

        encodings = ['utf-8']

        # check UTF BOMs
        bom_encodings = self._check_bom(self.content)
        if bom_encodings:
            encodings = list(set(enc.lower() for enc in bom_encodings + encodings))

        # add language-specific encodings
        # http://scratchpad.wikia.com/wiki/Character_Encoding_Recommendation_for_Languages

        if self.language.alpha3 == 'zho':
            encodings.extend(['cp936', 'gb2312', 'gbk', 'hz', 'iso2022_jp_2', 'cp950', 'big5hkscs', 'big5',
                              'gb18030', 'utf-16'])
        elif self.language.alpha3 == 'jpn':
            encodings.extend(['shift-jis', 'cp932', 'euc_jp', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2',
                              'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', ])
        elif self.language.alpha3 == 'tha':
            encodings.extend(['tis-620', 'cp874'])

        # arabian/farsi
        elif self.language.alpha3 in ('ara', 'fas', 'per'):
            encodings.extend(['windows-1256', 'utf-16', 'utf-16le', 'ascii', 'iso-8859-6'])
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
            encodings.extend(['windows-1252', 'iso-8859-15', 'iso-8859-9', 'iso-8859-4', 'iso-8859-1'])

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
        """Check if a :attr:`text` is a valid SubRip format. Note that original format will bypass the checking

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
                    if self.use_original_format:
                        self._og_format = subs.format
                        self._is_valid = True
                        return True

            except pysubs2.UnknownFPSError:
                # if parsing failed, use frame rate from provider
                sub_fps = self.get_fps()
                if not isinstance(sub_fps, float) or sub_fps < 10.0:
                    # or use our media file's fps as a fallback
                    sub_fps = self.plex_media_fps
                    logger.info("No FPS info in subtitle. Using our own media FPS for the MicroDVD subtitle: %s",
                                self.plex_media_fps)
                subs = pysubs2.SSAFile.from_string(text, fps=sub_fps)

            if not self.use_original_format:
                self.content = subs.to_string(format_="srt").encode(encoding=self.get_encoding())
            else:
                self.content = subs.to_string(format_=self.format)
        except:
            logger.exception("Couldn't convert subtitle %s to .srt format: %s", self, traceback.format_exc())
            return False

        self._is_valid = True
        return True

    def get_modified_content(self, format="srt", debug=False):
        """
        :return: string
        """
        if not self.mods:
            return fix_text(self.content.decode(encoding=self.get_encoding()), **ftfy_defaults).encode(
                encoding=self.get_encoding())

        submods = SubtitleModifications(debug=debug)
        if submods.load(content=self.text, language=self.language, mods=self.mods):
            logger.info("Applying mods: %s", self.mods)
            submods.modify(*self.mods)
            self.mods = submods.mods_used

            content = fix_text(submods.f.to_string(format_=format),
                               **ftfy_defaults).encode(encoding=self.get_encoding())
            submods.f = None
            del submods
            return content
        return None


class ModifiedSubtitle(Subtitle):
    id = None


MERGED_FORMATS = {
    "TV": ("HDTV", "SDTV", "AHDTV", "Ultra HDTV"),
    "Air": ("SATRip", "DVB", "PPV", "Digital TV"),
    "Disk-HD": ("HD-DVD", "Blu-ray", "Ultra HD Blu-ray"),
    "Disk-SD": ("DVD", "VHS"),
    "Web": ("Web",),
}

MERGED_FORMATS_REV = dict((v.lower(), k.lower()) for k in MERGED_FORMATS for v in MERGED_FORMATS[k])


def _has_match(video, guess, key) -> bool:
    value = getattr(video, key)
    guess_value = guess.get(key)

    # To avoid extra debug calls
    if guess_value is None or value is None:
        return False

    if isinstance(guess_value, list):
        matched = any(value == item for item in guess_value)
    else:
        matched = value == guess_value

    logger.debug("%s matched? %s (%s -> %s)", key, matched, value, guess_value)

    return matched


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
            if not isinstance(titles, list):
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
            episode = episode_guess = guess['episode']
            if isinstance(episode_guess, list):
                try:
                    episode = min([int(x) for x in episode_guess])
                except (TypeError, ValueError):
                    pass
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
        if not isinstance(release_groups, list):
            release_groups = [release_groups]

        if video.release_group:
            for release_group in release_groups:
                if (sanitize_release_group(release_group) in
                        get_equivalent_release_groups(sanitize_release_group(video.release_group))):
                    matches.add('release_group')
                    break
    # source
    if 'source' in guess:
        formats = guess["source"]
        if not isinstance(formats, list):
            formats = [formats]

        if video.source:
            video_format = video.source.lower()
            _video_gen_format = MERGED_FORMATS_REV.get(video_format)
            matched = False
            for frmt in formats:
                _guess_gen_frmt = MERGED_FORMATS_REV.get(frmt.lower())
                # We don't want to match a singleton
                if _guess_gen_frmt is None: # If the source is not in MERGED_FORMATS
                    _guess_gen_frmt = guess["source"]

                if _guess_gen_frmt == _video_gen_format:
                    matched = True
                    matches.add('source')
                    break

            logger.debug("Source match found? %s: %s -> %s", matched, video.source, formats)

        if "release_group" in matches and "source" not in matches:
            logger.info("Release group matched but source didn't. Removing release group match.")
            matches.remove("release_group")

    guess.update({"resolution": guess.get("screen_size")})

    # Solve match keys for potential lists
    for key in ("video_codec", "audio_codec", "edition", "streaming_service", "resolution"):
        if _has_match(video, guess, key):
            matches.add(key)

    for key in ("streaming_service", "edition", "other"):
        if _check_optional(video, guess, key):
            matches.add(key)

    return matches


def _check_optional(video, guess, key="edition"):
    guess_optional = guess.get(key)
    video_optional = getattr(video, key, None)

    if video_optional and guess_optional:
        return _has_match(video, guess, key)

    if not video_optional and not guess_optional:
        logger.debug("Both video and guess don't have %s. Returning True", key)
        return True

    logger.debug("One item doesn't have %s (%s -> %s). Returning False", key, guess_optional, video_optional)
    return False
