# -*- coding: utf-8 -*-

import logging
import os

from subzero.language import Language

from app.database import database, insert, update
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class CustomLanguage:
    """Base class for custom languages."""

    alpha2 = "pb"
    alpha3 = "pob"
    language = "pt-BR"
    official_alpha2 = "pt"
    official_alpha3 = "por"
    name = "Portuguese (Brazil)"
    iso = "BR"
    _scripts = []
    _possible_matches = ("pt-br", "pob", "pb", "brazilian", "brasil", "brazil")
    _extensions = (".pt-br", ".pob", ".pb")
    _extensions_forced = (".pt-br.forced", ".pob.forced", ".pb.forced")
    _extensions_hi = (".pt-br.hi", ".pob.hi", ".pb.hi",
                      ".pt-br.cc", ".pob.cc", ".pb.cc",
                      ".pt-br.sdh", ".pob.sdh", ".pb.sdh")

    def subzero_language(self):
        return Language(self.official_alpha3, self.iso)

    @classmethod
    def from_value(cls, value, attr="alpha3"):
        """Return a custom language subclass by value and attribute
        if found, otherwise return None.

        :param value:
        :param attr:
        """
        for sub in cls.__subclasses__():
            if getattr(sub, attr) == str(value):
                return sub()

        return None

    @classmethod
    def register(cls, table):
        """Register the custom language subclasses in the database."""

        for sub in cls.__subclasses__():
            try:
                database.execute(
                    insert(table)
                    .values(code3=sub.alpha3,
                            code2=sub.alpha2,
                            name=sub.name,
                            enabled=0))
            except IntegrityError:
                database.execute(
                    update(table)
                    .values(code2=sub.alpha2,
                            name=sub.name)
                    .where(table.code3 == sub.alpha3))

    @classmethod
    def found_external(cls, subtitle, subtitle_path):
        for sub in cls.__subclasses__():
            code = sub.get_alpha_type(subtitle, subtitle_path)
            if code:
                return code

        return None

    @classmethod
    def get_alpha_type(cls, subtitle: str, subtitle_path=None):

        extension = str(os.path.splitext(subtitle)[0]).lower()
        to_return = None

        if extension.endswith(cls._extensions):
            to_return = cls.alpha2

        if extension.endswith(cls._extensions_forced):
            to_return = f"{cls.alpha2}:forced"

        if extension.endswith(cls._extensions_hi):
            to_return = f"{cls.alpha2}:HI"

        if to_return is not None:
            logging.debug("BAZARR external subtitles detected: %s", to_return)

        return to_return

    def ffprobe_found(self, detected_language: dict) -> bool:
        name = detected_language.get("name", "").lower()
        if not name:
            return False

        return any(ext in name for ext in self._possible_matches)

    def language_found(self, language: Language):
        if str(language.country) == self.iso:
            return True

        if language.script and str(language.script) in self._scripts:
            return True

        return False


class BrazilianPortuguese(CustomLanguage):
    # Same attributes as base class
    pass


class Portuguese(CustomLanguage):
    alpha2 = "pt"
    alpha3 = "por"
    language = "pt-PT"
    official_alpha2 = "pt"
    official_alpha3 = "por"
    name = "Portuguese"
    iso = "PT"
    _scripts = []
    _possible_matches = ("pt-pt", "por", "pt")
    _extensions = (".pt-pt", ".por", ".pt")
    _extensions_forced = (".pt-pt.forced", ".por.forced", ".pt.forced")
    _extensions_hi = (".pt-pt.hi", ".por.hi", ".pt.hi",
                      ".pt-pt.cc", ".por.cc", ".pt.cc",
                      ".pt-pt.sdh", ".por.sdh", ".pt.sdh")

    def subzero_language(self):
        return Language(self.official_alpha3)

    def language_found(self, language: Language):
        return str(language.alpha3) == self.alpha3


class ChineseTraditional(CustomLanguage):
    alpha2 = "zt"
    alpha3 = "zht"
    language = "zh-TW"
    official_alpha2 = "zh"
    official_alpha3 = "zho"
    name = "Chinese Traditional"
    iso = "TW"
    # _scripts = (Script("Hant"),)
    # We'll use literals for now
    _scripts = ("Hant",)
    _extensions = (
        ".cht", ".tc", ".zh-tw", ".zht", ".zh-hant", ".zhhant", ".zh_hant", ".hant", ".big5", ".traditional",
    )
    _extensions_forced = (
        ".cht.forced", ".tc.forced", ".zht.forced", "hant.forced", ".big5.forced", "繁體中文.forced", "雙語.forced",
        ".zh-tw.forced",
    )
    _extensions_hi = (
        ".cht.hi", ".tc.hi", ".zht.hi", "hant.hi", ".big5.hi", "繁體中文.hi", "雙語.hi", ".zh-tw.hi",
        ".cht.cc", ".tc.cc", ".zht.cc", "hant.cc", ".big5.cc", "繁體中文.cc", "雙語.cc", ".zh-tw.cc",
        ".cht.sdh", ".tc.sdh", ".zht.sdh", "hant.sdh", ".big5.sdh", "繁體中文.sdh", "雙語.sdh", ".zh-tw.sdh",
    )
    _extensions_fuzzy = ("繁", "雙語")
    _extensions_disamb_fuzzy = ("简", "双语")
    _extensions_disamb = (
        ".chs", ".sc", ".zhs", ".zh-hans", ".hans", ".zh_hans", ".zhhans", ".gb", ".simplified",
    )
    _extensions_disamb_forced = (
        ".chs.forced", ".sc.forced", ".zhs.forced", "hans.forced", ".gb.forced", "简体中文.forced", "双语.forced",
    )
    _extensions_disamb_hi = (
        ".chs.hi", ".sc.hi", ".zhs.hi", "hans.hi", ".gb.hi", "简体中文.hi", "双语.hi",
        ".chs.cc", ".sc.cc", ".zhs.cc", "hans.cc", ".gb.cc", "简体中文.cc", "双语.cc",
        ".chs.sdh", ".sc.sdh", ".zhs.sdh", "hans.sdh", ".gb.sdh", "简体中文.sdh", "双语.sdh",
    )

    @classmethod
    def get_alpha_type(cls, subtitle, subtitle_path=None):
        subtitle_path = str(subtitle_path).lower()
        extension = str(os.path.splitext(subtitle)[0]).lower()

        to_return = None

        # Simplified chinese
        if (
            extension.endswith(cls._extensions_disamb)
            or subtitle_path in cls._extensions_disamb_fuzzy
        ):
            to_return = "zh"

        elif any(ext in extension[-12:] for ext in cls._extensions_disamb_forced):
            to_return = "zh:forced"

        elif any(ext in extension[-12:] for ext in cls._extensions_disamb_hi):
            to_return = "zh:HI"

        # Traditional chinese
        elif (
            extension.endswith(cls._extensions)
            or subtitle_path[:-5] in cls._extensions_fuzzy
        ):
            to_return = "zt"

        elif any(ext in extension[-12:] for ext in cls._extensions_forced):
            to_return = "zt:forced"

        elif any(ext in extension[-12:] for ext in cls._extensions_hi):
            to_return = "zt:HI"

        if to_return is not None:
            logging.debug("BAZARR external subtitles detected: %s", to_return)

        return to_return


class LatinAmericanSpanish(CustomLanguage):
    alpha2 = "ea"  # Only one available I can think of
    alpha3 = "spl"
    language = "es-MX"
    official_alpha2 = "es"
    official_alpha3 = "spa"
    name = "Spanish (Latino)"
    iso = "MX"  # Not fair, but ok
    _scripts = ("419",)
    _possible_matches = (
        "es-la", "spa-la", "spl", "mx", "latin", "mexic", "argent", "latam",
    )
    _extensions = (".es-la", ".spl", ".spa-la", ".ea", ".es-mx", ".lat", ".es.ar")
    _extensions_forced = (
        ".es-la.forced", ".spl.forced", ".spa-la.forced", ".ea.forced", ".es-mx.forced", ".lat.forced", ".es.ar.forced",
    )
    _extensions_hi = (
        ".es-la.hi", ".spl.hi", ".spa-la.hi", ".ea.hi", ".es-mx.hi", ".lat.hi", ".es.ar.hi",
        ".es-la.cc", ".spl.cc", ".spa-la.cc", ".ea.cc", ".es-mx.cc", ".lat.cc", ".es.ar.cc",
        ".es-la.sdh", ".spl.sdh", ".spa-la.sdh", ".ea.sdh", ".es-mx.sdh", ".lat.sdh", ".es.ar.sdh",
    )
