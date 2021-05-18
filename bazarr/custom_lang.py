# -*- coding: utf-8 -*-

import logging
import os

from subzero.language import Language

logger = logging.getLogger(__name__)


class CustomLanguage:
    """Base class for custom languages."""

    alpha2 = "pb"
    alpha3 = "pob"
    language = "pt-BR"
    official_alpha2 = "pt"
    official_alpha3 = "por"
    name = "Brazilian Portuguese"
    iso = "BR"
    _possible_matches = ("pt-br", "pob", "pb", "brazilian", "brasil", "brazil")
    _extensions = (".pt-br", ".pob", ".pb")
    _extensions_forced = (".pt-br.forced", ".pob.forced", ".pb.forced")

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
    def register(cls, database):
        " Register the custom language subclasses in the database. "

        for sub in cls.__subclasses__():
            params = (sub.alpha3, sub.alpha2, sub.name)
            database.execute(
                "INSERT OR IGNORE INTO table_settings_languages "
                "(code3, code2, name) VALUES (?,?,?)",
                params,
            )

    @classmethod
    def found_external(cls, subtitle, subtitle_path):
        for sub in cls.__subclasses__():
            code = sub.get_alpha_type(subtitle, subtitle_path)
            if code:
                return code

        return None

    @classmethod
    def get_alpha_type(cls, subtitle: str, subtitle_path=None):
        assert subtitle_path is not None

        extension = str(os.path.splitext(subtitle)[0]).lower()
        to_return = None

        if extension.endswith(cls._extensions):
            to_return = cls.alpha2

        if extension.endswith(cls._extensions_forced):
            to_return = f"{cls.alpha2}:forced"

        if to_return is not None:
            logging.debug("BAZARR external subtitles detected: %s", to_return)

        return to_return

    def ffprobe_found(self, detected_language: dict) -> bool:
        name = detected_language.get("name", "").lower()
        if not name:
            return False

        return any(ext in name for ext in self._possible_matches)


class BrazilianPortuguese(CustomLanguage):
    pass


class ChineseTraditional(CustomLanguage):
    alpha2 = "zt"
    alpha3 = "zht"
    language = "zh-TW"
    official_alpha2 = "zh"
    official_alpha3 = "zho"
    name = "Chinese Traditional"
    iso = "TW"
    _extensions = (
        ".cht",
        ".tc",
        ".zh-tw",
        ".zht",
        ".zh-hant",
        ".zhhant",
        ".zh_hant",
        ".hant",
        ".big5",
        ".traditional",
    )
    _extensions_forced = (
        ".cht.forced",
        ".tc.forced",
        ".zht.forced",
        "hant.forced",
        ".big5.forced",
        "繁體中文.forced",
        "雙語.forced",
        ".zh-tw.forced",
    )
    _extensions_fuzzy = ("繁", "雙語")
    _extensions_disamb_fuzzy = ("简", "双语")
    _extensions_disamb = (
        ".chs",
        ".sc",
        ".zhs",
        ".zh-hans",
        ".hans",
        ".zh_hans",
        ".zhhans",
        ".gb",
        ".simplified",
    )
    _extensions_disamb_forced = (
        ".chs.forced",
        ".sc.forced",
        ".zhs.forced",
        "hans.forced",
        ".gb.forced",
        "简体中文.forced",
        "双语.forced",
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

        # Traditional chinese
        elif (
            extension.endswith(cls._extensions)
            or subtitle_path[:-5] in cls._extensions_fuzzy
        ):
            to_return = "zt"

        elif any(ext in extension[-12:] for ext in cls._extensions_forced):
            to_return = "zt:forced"

        if to_return is not None:
            logging.debug("BAZARR external subtitles detected: %s", to_return)

        return to_return


class LatinAmericanSpanish(CustomLanguage):
    alpha2 = "ea"  # Only one available I can think of
    alpha3 = "spl"
    language = "es-LA"
    official_alpha2 = "es"
    official_alpha3 = "spa"
    name = "Latin American Spanish"
    iso = "MX"  # Not fair, but ok
    _possible_matches = (
        "es-la",
        "spa-la",
        "spl",
        "mx",
        "latin",
        "mexic",
        "argent",
        "latam",
    )
    _extensions = (".es-la", ".spl", ".spa-la", ".ea", ".es-mx", ".lat", ".es.ar")
    _extensions_forced = (
        ".es-la.forced",
        ".spl.forced",
        ".spa-la.forced",
        ".ea.forced",
        ".es-mx.forced",
        ".lat.forced",
        ".es.ar.forced",
    )
