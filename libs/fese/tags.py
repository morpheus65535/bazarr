from datetime import timedelta
import logging

from babelfish import Language
from babelfish.exceptions import LanguageError

from .exceptions import LanguageNotFound

logger = logging.getLogger(__name__)

LANGUAGE_FALLBACK = None


class FFprobeGenericSubtitleTags:
    _DETECTABLE_TAGS = None

    def __init__(self, data: dict):
        self._language_fallback = False

        try:
            self.language = _get_language(data)
        except LanguageNotFound:
            if LANGUAGE_FALLBACK is not None:
                self.language = Language.fromietf(LANGUAGE_FALLBACK)
                self._language_fallback = True
            else:
                raise

        self._data = data

    @classmethod
    def detect_cls_from_data(cls, data):
        for cls_ in (FFprobeMkvSubtitleTags, FFprobeMp4SubtitleTags):
            if cls_.is_compatible(data):
                logger.debug("Detected tags class: %s", cls_)
                return cls_(data)

        logger.debug("Unable to detect tags class. Using generic")
        return FFprobeGenericSubtitleTags(data)

    @property
    def language_fallback(self):
        return self._language_fallback

    @property
    def suffix(self):
        lang = self.language.alpha2
        if self.language.country is not None:
            lang = f"{lang}-{self.language.country}"

        return str(lang)

    @property
    def frames(self):
        return 0

    @classmethod
    def is_compatible(cls, data):
        return False

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.suffix}"


class FFprobeMkvSubtitleTags(FFprobeGenericSubtitleTags):
    _DETECTABLE_TAGS = (
        "BPS",
        "BPS-eng",
        "DURATION",
        "DURATION-eng",
        "NUMBER_OF_FRAMES",
        "NUMBER_OF_FRAMES-eng",
        "NUMBER_OF_BYTES",
        "NUMBER_OF_BYTES-eng",
    )

    def __init__(self, data: dict):
        super().__init__(data)

        self.title = data.get("title")
        self.bps = _safe_int(data.get("BPS"))
        self.bps_eng = _safe_int(data.get("BPS-eng"))
        self.duration = _safe_td(data.get("DURATION"))
        self.duration_eng = _safe_td(data.get("DURATION-eng"))
        self.number_of_frames = _safe_int(data.get("NUMBER_OF_FRAMES"))
        self.number_of_frames_eng = _safe_int(data.get("NUMBER_OF_FRAMES-eng"))
        self.number_of_bytes = _safe_int(data.get("NUMBER_OF_BYTES"))
        self.number_of_bytes_eng = _safe_int(data.get("NUMBER_OF_BYTES-eng"))

    @property
    def frames(self):
        return self.number_of_frames or self.number_of_frames_eng or 0

    @classmethod
    def is_compatible(cls, data):
        return any(
            key
            in (
                "BPS",
                "BPS-eng",
                "DURATION",
                "DURATION-eng",
                "NUMBER_OF_FRAMES",
                "NUMBER_OF_FRAMES-eng",
                "NUMBER_OF_BYTES",
                "NUMBER_OF_BYTES-eng",
            )
            for key in data.keys()
        )


class FFprobeMp4SubtitleTags(FFprobeGenericSubtitleTags):
    _DETECTABLE_TAGS = ("creation_time", "handler_name")

    def __init__(self, data: dict):
        super().__init__(data)
        self.creation_time = data.get("creation_time")
        self.handler_name = data.get("handler_name")

    @classmethod
    def is_compatible(cls, data):
        return any(key in ("creation_time", "handler_name") for key in data.keys())


def _get_language(tags) -> Language:
    og_lang = tags.get("language")
    last_exc = None

    if og_lang is not None:
        if og_lang in _extra_languages:
            extra = _extra_languages[og_lang]
            title = tags.get("title", "n/a").lower()
            if any(possible in title for possible in extra["matches"]):
                logger.debug("Found extra language %s", extra["language_args"])
                return Language(*extra["language_args"])

        try:
            if len(og_lang) == 3:
                lang = Language.fromalpha3b(og_lang)
            else:
                lang = Language.fromalpha2(og_lang[:2])

            # Test for suffix
            assert lang.alpha2

            return lang
        except LanguageError as error:
            last_exc = error
            logger.debug("Error with '%s' language: %s", og_lang, error)

    raise LanguageNotFound(f"Couldn't detect language from tags: {tags}") from last_exc


def _safe_td(value, default=None):
    if value is None:
        return default

    try:
        h, m, s = [float(ts.replace(",", ".").strip()) for ts in value.split(":")]
        return timedelta(hours=h, minutes=m, seconds=s)
    except ValueError as error:
        logger.warning("Couldn't get duration field: %s. Returning %s", error, default)
        return default


def _safe_int(value, default=None):
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        logger.warning("Couldn't convert to int: %s. Returning %s", value, default)
        return default


_extra_languages = {
    "spa": {
        "matches": (
            "es-la",
            "spa-la",
            "spl",
            "mx",
            "latin",
            "mexic",
            "argent",
            "latam",
        ),
        "language_args": ("spa", "MX"),
    },
    "por": {
        "matches": ("pt-br", "pob", "pb", "brazilian", "brasil", "brazil"),
        "language_args": ("por", "BR"),
    },
}
